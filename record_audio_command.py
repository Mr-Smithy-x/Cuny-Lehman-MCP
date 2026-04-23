# Captures mic input and saves to a WAV file
import sounddevice as sd
import soundfile as sf
# server.py using the MCP Python SDK
from mcp.server import FastMCP
from mcp.server.fastmcp import Audio
from f5_tts.api import F5TTS as tts

app = FastMCP("voice-tts")


@app.tool()
async def record_voice(duration: int = 10, output_path: str = "my_voice.wav") -> Audio:
    """Record voice sample for cloning (10 seconds recommended)"""
    sample_rate = 24000
    device_info = sd.query_devices(None, "input")
    print(f"Recording for {duration} seconds...")
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, device=device_info['index'])
    sd.wait()
    sf.write(output_path, audio, sample_rate)
    return Audio(output_path, audio.data, format="wav")
    #return {"path": output_path, "duration": duration}

@app.tool()
async def synthesize_speech(
    text: str,
    reference_audio: str = "my_voice.wav",
    reference_text: str = "",   # optional transcript of reference audio
    output_path: str = "output.wav"
) -> dict:
    """Generate speech in the cloned voice using F5-TTS"""
    wav, sr, _ = tts.infer(
        ref_file=reference_audio,
        ref_text=reference_text,  # leave empty for auto-transcription
        gen_text=text,
        file_wave=output_path
    )
    return {"output": output_path, "sample_rate": sr}


if __name__ == "__main__":
    app.run()
    #sd.query_devices("MacBook Air Microphone")
    #print(sd.query_devices("MacBook Air Microphone"))
    print(sd.query_devices(None, "input"))