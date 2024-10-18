import os
import subprocess
import string
import gradio as gr
from docx import Document
from PyPDF2 import PdfReader

UPLOAD_FOLDER = 'uploads'

# Hàm đọc từ điển ngữ âm (lexicon)
def load_lexicon(lexicon_file):
    lexicon = set()
    with open(lexicon_file, 'r', encoding='utf-8') as f:
        for line in f:
            word = line.split()[0].lower()  # Chuyển tất cả các từ trong từ điển sang chữ thường
            lexicon.add(word)
    return lexicon

# Hàm đọc file Word
def read_word(file_path):
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

# Hàm đọc file PDF
def read_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Hàm tiền xử lý văn bản, chỉ giữ lại các từ có trong từ điển ngữ âm
def preprocess_text(text, lexicon):
    words = text.split()
    valid_words = []
    
    for word in words:
        clean_word = word.strip(string.punctuation).lower()
        if clean_word in lexicon or word in string.punctuation:
            valid_words.append(word)
        elif word[0].isupper():  # Giữ lại các từ viết hoa (có thể là tên riêng)
            valid_words.append(word)
        elif len(clean_word) > 1:  # Giữ lại các từ có độ dài > 1
            valid_words.append(word)
    
    return ' '.join(valid_words)


# Hàm chuyển văn bản sang giọng nói sử dụng vietTTS
def text_to_speech(text):
    output_path = 'output.wav'
    command = [
        'python', '-m', 'vietTTS.synthesizer',
        '--lexicon-file=assets/infore/lexicon.txt',
        '--text', text,
        '--output', os.path.join(os.getcwd(), output_path)
    ]
    try:
        subprocess.run(command, check=True)
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error during text-to-speech conversion: {e}")
        return None

def process_input(file=None, text_input=""):
    if file is not None:
        # Xác định loại file dựa trên nội dung bytes
        if file.startswith(b'%PDF'):
            file_extension = '.pdf'
        elif file.startswith(b'PK\x03\x04'):
            file_extension = '.docx'
        else:
            return "Unsupported file type.", None

        # Tạo tên file tạm thời
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(file)
            temp_file_path = temp_file.name

        # Đọc nội dung file
        if file_extension == '.docx':
            text = read_word(temp_file_path)
        elif file_extension == '.pdf':
            text = read_pdf(temp_file_path)
        
        # Xóa file tạm sau khi đã đọc
        os.unlink(temp_file_path)
    elif text_input:
        text = text_input
    else:
        return "No input provided.", None

    lexicon = load_lexicon('assets/infore/lexicon.txt')
    processed_text = preprocess_text(text, lexicon)
    
    # Chuyển đổi văn bản thành giọng nói
    output_audio = text_to_speech(processed_text)
    if output_audio is None:
        return "Error during text-to-speech conversion.", None
    return output_audio

# Tạo giao diện với Gradio
iface = gr.Interface(
    fn=process_input,
    inputs=[gr.File(label="Upload a Word/PDF File", type="binary"), gr.Textbox(lines=5, placeholder="Or enter text manually")],
    outputs=gr.Audio(label="Generated Speech"),
    title="Text to Speech Converter(HQC)",
    description="Upload a Word/PDF file or enter text, and convert it to speech."
)

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    iface.launch(share=False)
