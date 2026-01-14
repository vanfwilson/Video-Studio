from app.services.captions import generate_captions

def process_video_file(filepath: str):
    print(f"Processing file: {filepath}")
    transcription = generate_captions(filepath)
    print(f"Caption complete: {transcription}")
