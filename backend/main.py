from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import whisper
from docx import Document
import os
import asyncio
from typing import Dict
import uuid
from datetime import datetime, timedelta
from pydub import AudioSegment
from moviepy.editor import AudioFileClip
import torch

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store job status
JOBS: Dict[str, Dict] = {}


def update_job_status(
    job_id: str, stage: str, current: int = 0, total_chunks: int = 0, message: str = ""
):
    """Update job status with detailed progress information"""
    if job_id in JOBS:
        JOBS[job_id].update(
            {
                "status": "processing",
                "progress": {
                    "stage": stage,
                    "current_chunk": current,
                    "total_chunks": total_chunks,
                    "message": message,
                },
            }
        )


def cleanup_old_jobs():
    """Remove jobs older than 24 hours"""
    now = datetime.now()
    for job_id in list(JOBS.keys()):
        if now - JOBS[job_id]["timestamp"] > timedelta(hours=24):
            del JOBS[job_id]


async def split_audio(file_path: str, chunk_duration: int = 120000) -> list:
    """Split audio file into chunks"""
    audio = AudioSegment.from_file(file_path)
    chunks = []

    # Optimize audio before splitting
    audio = audio.set_channels(1)  # Convert to mono
    audio = audio.set_frame_rate(16000)  # Reduce sample rate

    for i in range(0, len(audio), chunk_duration):
        chunk = audio[i : i + chunk_duration]
        chunk_path = f"{file_path}_chunk_{i//chunk_duration}.wav"
        chunk.export(
            chunk_path,
            format="wav",
            parameters=["-q:a", "0", "-ar", "16000"],  # Optimize export
        )
        chunks.append(chunk_path)
        del chunk  # Free memory

    del audio  # Free memory
    return chunks


async def process_audio(job_id: str, file_path: str, output_path: str):
    try:
        transcriptions = []
        total_steps = 4
        current_step = 1

        # Fase 1: Caricamento modello
        update_job_status(
            job_id,
            "loading_model",
            current=current_step,
            total_chunks=total_steps,
            message="Fase 1/4: Caricamento modello di intelligenza artificiale su GPU...",
        )

        if torch.cuda.is_available():
            # Massimizza l'utilizzo della GPU
            torch.cuda.empty_cache()
            torch.backends.cudnn.benchmark = True
            torch.backends.cudnn.enabled = True
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            torch.cuda.set_device(0)  # Forza l'uso della GPU principale
            print(f"Using GPU: {torch.cuda.get_device_name(0)}")

        # Carica il modello medium per bilanciare velocità e accuratezza
        model = whisper.load_model("small")
        if torch.cuda.is_available():
            model = model.cuda()
            model.eval()  # Imposta modalità valutazione
            torch._C._jit_set_bailout_depth(20)  # Ottimizza JIT
            model = torch.compile(model, mode="max-autotune", fullgraph=True)

        # Fase 2: Splitting audio
        current_step += 1
        update_job_status(
            job_id,
            "splitting_audio",
            current=current_step,
            total_chunks=total_steps,
            message="Fase 2/4: Divisione dell'audio in segmenti...",
        )

        # Chunk più grandi per sfruttare meglio la GPU
        chunks = await split_audio(file_path, chunk_duration=300000)  # 5 minuti

        # Fase 3: Trascrizione
        current_step += 1
        update_job_status(
            job_id,
            "transcribing",
            current=current_step,
            total_chunks=len(chunks),
            message=f"Fase 3/4: Inizio trascrizione con GPU",
        )

        # Batch processing ottimizzato per GPU
        for i, chunk in enumerate(chunks):
            try:
                # Forza sincronizzazione GPU prima di ogni chunk
                if torch.cuda.is_available():
                    torch.cuda.synchronize()
                    torch.cuda.empty_cache()

                with torch.cuda.amp.autocast(
                    enabled=True, dtype=torch.float16, cache_enabled=True
                ):
                    with torch.inference_mode():
                        with torch.backends.cuda.sdp_kernel(
                            enable_flash=True,
                            enable_math=True,
                            enable_mem_efficient=True,
                        ):
                            result = model.transcribe(
                                chunk,
                                fp16=True,
                                language="italian",
                                initial_prompt="Questa è una trascrizione di un audio in italiano.",
                                temperature=0.0,
                                no_speech_threshold=0.6,
                                compression_ratio_threshold=2.4,
                                condition_on_previous_text=True,
                                beam_size=5,  # Aumentato per sfruttare la GPU
                                best_of=5,  # Aumentato per sfruttare la GPU
                                without_timestamps=True,
                            )
                        transcriptions.append(result["text"])

                os.remove(chunk)

                # Forza sincronizzazione dopo ogni chunk
                if torch.cuda.is_available():
                    torch.cuda.synchronize()

                update_job_status(
                    job_id,
                    "transcribing",
                    i + 1,
                    len(chunks),
                    f"Trascrizione segmento {i+1} di {len(chunks)}",
                )

            except Exception as e:
                print(f"Errore nel chunk {i}: {str(e)}")

        # Fase 4: Formattazione
        current_step += 1
        update_job_status(
            job_id,
            "formatting",
            current=current_step,
            total_chunks=total_steps,
            message="Fase 4/4: Formattazione del documento finale...",
        )

        update_job_status(job_id, "formatting", message="Formattazione del testo...")
        full_text = "\n\n".join(transcriptions)
        formatted_text = format_transcription(full_text)

        update_job_status(
            job_id, "creating_document", message="Creazione del documento Word..."
        )

        # Crea il documento Word
        doc = Document()
        doc.add_heading("Trascrizione Audio", 0)
        doc.add_paragraph(
            f'Data trascrizione: {datetime.now().strftime("%d/%m/%Y %H:%M")}'
        )
        doc.add_paragraph(f'File originale: {JOBS[job_id]["filename"]}')
        doc.add_paragraph("")

        for paragraph in formatted_text.split("\n"):
            if paragraph.strip():
                p = doc.add_paragraph(paragraph.strip())
                p.paragraph_format.line_spacing = 1.5

        doc.save(output_path)

        JOBS[job_id]["status"] = "completed"
        JOBS[job_id]["output_path"] = output_path

    except Exception as e:
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["error"] = str(e)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


def format_transcription(text: str) -> str:
    """Migliora la formattazione del testo trascritto"""
    import re

    # Correggi la punteggiatura comune
    text = re.sub(r"\s+([.,!?])", r"\1", text)
    text = re.sub(r"([.,!?])([A-Z])", r"\1\n\n\2", text)

    # Gestisci le pause nel parlato
    text = re.sub(r"\s*\.\.\.\s*", "...\n", text)

    # Aggiungi virgole prima delle congiunzioni
    conjunctions = r"\s+(e|ma|però|quindi|perché|quando|se)\s+"
    text = re.sub(conjunctions, lambda m: f", {m.group(1)} ", text)

    # Correggi la formattazione dei dialoghi
    text = re.sub(r'"([^"]+)"', r'"\1"', text)

    # Aggiungi spazi dopo la punteggiatura
    text = re.sub(r"([.,!?])([^\s])", r"\1 \2", text)

    return text


@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks()
):
    cleanup_old_jobs()

    # List of supported audio formats
    supported_formats = [".m4a", ".mp3", ".wav", ".aac", ".wma", ".ogg"]
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in supported_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Formato file non supportato. Formati supportati: {', '.join(supported_formats)}",
        )

    # Generate unique job ID
    job_id = str(uuid.uuid4())

    try:
        # Create temp and output directories if they don't exist
        os.makedirs("temp", exist_ok=True)
        os.makedirs("output", exist_ok=True)

        # Save file
        file_path = f"temp/{job_id}_{file.filename}"
        output_path = f"output/{job_id}_{file.filename}.docx"

        with open(file_path, "wb") as buffer:
            # Read in chunks to handle large files
            chunk_size = 1024 * 1024  # 1MB chunks
            while chunk := await file.read(chunk_size):
                buffer.write(chunk)

        # Initialize job status
        JOBS[job_id] = {
            "status": "processing",
            "timestamp": datetime.now(),
            "filename": file.filename,
            "progress": {
                "stage": "initializing",
                "current_chunk": 0,
                "total_chunks": 0,
                "message": "Inizializzazione del processo...",
            },
        }

        # Start processing in background
        background_tasks.add_task(process_audio, job_id, file_path, output_path)

        return JSONResponse({"job_id": job_id, "status": "processing"})

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job non trovato")
    return JOBS[job_id]


@app.get("/download/{job_id}")
async def download_file(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found")

    job = JOBS[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="File not ready")

    return FileResponse(job["output_path"], filename=f"{job['filename']}.docx")
