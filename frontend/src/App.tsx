import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
    const [file, setFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [progress, setProgress] = useState<number>(0);
    const [error, setError] = useState<string>('');
    const [jobId, setJobId] = useState<string | null>(null);
    const [processingStatus, setProcessingStatus] = useState<string>('');
    const [processingDetails, setProcessingDetails] = useState<{
        stage: string;
        current_chunk: number;
        total_chunks: number;
        message: string;
    }>({
        stage: '',
        current_chunk: 0,
        total_chunks: 0,
        message: ''
    });

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            setFile(e.target.files[0]);
        }
    };

    const checkJobStatus = async (id: string) => {
        try {
            const response = await axios.get(`http://localhost:8000/status/${id}`);
            const { status, progress } = response.data;

            if (progress) {
                setProcessingDetails(progress);
                setProcessingStatus(progress.message);
            }

            if (status === 'completed') {
                await downloadResult(id);
            } else if (status === 'failed') {
                setError(response.data.error || 'Trascrizione fallita');
                setLoading(false);
            } else {
                const delay = progress?.stage === 'transcribing' ? 500 : 1000;
                setTimeout(() => checkJobStatus(id), delay);
            }
        } catch (error) {
            setError('Errore nel controllo dello stato');
            setLoading(false);
        }
    };

    const downloadResult = async (id: string) => {
        try {
            const response = await axios.get(`http://localhost:8000/download/${id}`, {
                responseType: 'blob'
            });

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `${file?.name}.docx`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);

            setLoading(false);
            setJobId(null);
        } catch (error) {
            setError('Errore nel download del file');
            setLoading(false);
        }
    };

    const handleSubmit = async () => {
        if (!file) {
            setError('Seleziona un file audio prima di procedere');
            return;
        }

        try {
            setLoading(true);
            setError('');

            // File size check
            if (file.size > 100 * 1024 * 1024) {
                throw new Error('Il file non può superare i 100MB');
            }

            const formData = new FormData();
            formData.append('file', file);

            const response = await axios.post('http://localhost:8000/transcribe', formData, {
                onUploadProgress: (progressEvent) => {
                    const percentCompleted = Math.round(
                        (progressEvent.loaded * 100) / (progressEvent.total || file.size)
                    );
                    setProgress(percentCompleted);
                },
                timeout: 3600000,
            });

            setJobId(response.data.job_id);
            checkJobStatus(response.data.job_id);
        } catch (error) {
            console.error('Error during transcription:', error);
            setError(error instanceof Error ?
                error.message :
                'Si è verificato un errore durante la trascrizione');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container">
            <h1>Audio Transcription App</h1>
            <input
                type="file"
                accept=".m4a,.mp3,.wav,.aac,.wma,.ogg"
                onChange={handleFileUpload}
            />
            <button onClick={handleSubmit} disabled={!file || loading}>
                {loading ? 'Trascrizione in corso...' : 'Avvia Trascrizione'}
            </button>
            {loading && (
                <>
                    <div className="progress-container">
                        <div className="progress-bar">
                            <div
                                className="progress-bar-fill"
                                style={{
                                    width: processingDetails.total_chunks > 0
                                        ? `${(processingDetails.current_chunk / processingDetails.total_chunks) * 100}%`
                                        : `${progress}%`
                                }}
                            />
                        </div>
                        <div className="progress-text">
                            {processingDetails.total_chunks > 0
                                ? `${Math.round((processingDetails.current_chunk / processingDetails.total_chunks) * 100)}%`
                                : progress === 100 ? 'Elaborazione in corso...' : `Caricamento: ${progress}%`}
                        </div>
                    </div>
                    <div className="processing-status">
                        <h3>{processingDetails.stage === 'transcribing' ? 'Trascrizione in corso' : 'Preparazione'}</h3>
                        <p className="status-message">{processingStatus || 'Inizializzazione...'}</p>
                        {processingDetails.total_chunks > 0 && processingDetails.stage === 'transcribing' && (
                            <div className="detailed-progress">
                                <div className="chunk-status">
                                    Segmento {processingDetails.current_chunk} di {processingDetails.total_chunks}
                                </div>
                            </div>
                        )}
                    </div>
                </>
            )}
            {error && <div className="error-message">{error}</div>}
        </div>
    );
}

export default App;