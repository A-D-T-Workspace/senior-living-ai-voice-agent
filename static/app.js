const statusElement = document.getElementById("status");
const recordButton = document.getElementById("recordButton");
const stopButton = document.getElementById("stopButton");
const callerText = document.getElementById("callerText");
const agentResponse = document.getElementById("agentResponse");

let sessionId = null;
let mediaRecorder = null;
let audioChunks = [];
let audioStream = null;

async function initializeSession() {
    try {
        statusElement.textContent = "Creating conversation session...";

        const response = await fetch("/sessions", {
            method: "POST"
        });

        if (!response.ok) {
            throw new Error("Could not create conversation session.");
        }

        const data = await response.json();
        sessionId = data.session_id;

        statusElement.textContent = "Ready. You can start speaking.";
        recordButton.disabled = false;

    } catch (error) {
        statusElement.textContent = error.message;
    }
}

async function startRecording() {
    try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error("Your browser does not support microphone recording.");
        }

        audioStream = await navigator.mediaDevices.getUserMedia({
            audio: true
        });

        let options = {};

        if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
            options.mimeType = "audio/webm;codecs=opus";
        } else if (MediaRecorder.isTypeSupported("audio/webm")) {
            options.mimeType = "audio/webm";
        } else if (MediaRecorder.isTypeSupported("audio/mp4")) {
            options.mimeType = "audio/mp4";
        }

        mediaRecorder = new MediaRecorder(audioStream, options);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = uploadRecording;

        mediaRecorder.start();

        recordButton.disabled = true;
        stopButton.disabled = false;

        statusElement.textContent = "Listening... Speak now.";

    } catch (error) {
        statusElement.textContent = `Microphone error: ${error.message}`;
        stopMicrophone();
    }
}

function stopMicrophone() {
    if (audioStream) {
        audioStream.getTracks().forEach(track => track.stop());
        audioStream = null;
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
        stopMicrophone();

        stopButton.disabled = true;
        statusElement.textContent = "Processing your message...";
    }
}

async function uploadRecording() {
    try {
        const mimeType = mediaRecorder.mimeType || "audio/webm";
        const audioBlob = new Blob(audioChunks, {
            type: mimeType
        });

        if (audioBlob.size === 0) {
            throw new Error("No audio was recorded. Please try again.");
        }

        const extension = mimeType.includes("mp4") ? "mp4" :
            mimeType.includes("ogg") ? "ogg" :
            mimeType.includes("wav") ? "wav" : "webm";

        const formData = new FormData();

        formData.append("session_id", sessionId);
        formData.append(
            "audio",
            audioBlob,
            `recording.${extension}`
        );

        const response = await fetch("/voice/process", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Voice processing failed.");
        }

        const caller = response.headers.get("X-Caller-Text");
        const assistant = response.headers.get("X-Agent-Response");

        callerText.textContent = caller || "No transcription available.";
        agentResponse.textContent = assistant || "No response available.";

        const responseAudio = await response.blob();
        const audioUrl = URL.createObjectURL(responseAudio);

        const player = new Audio(audioUrl);

        player.onended = () => URL.revokeObjectURL(audioUrl);

        await player.play();

        statusElement.textContent = "Response delivered. You can speak again.";

    } catch (error) {
        statusElement.textContent = error.message;

    } finally {
        recordButton.disabled = false;
        stopButton.disabled = true;
    }
}

recordButton.addEventListener("click", startRecording);
stopButton.addEventListener("click", stopRecording);

initializeSession();