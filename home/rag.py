import PyPDF2
import faiss
import google.generativeai as genai
import os

# Cấu hình API key của Gemini
genai.configure(api_key="AIzaSyDeKpc5dNwtaQWQqA45B90-mU4jWHcwIWA")
model = genai.GenerativeModel("gemini-1.5-flash")


# Hàm trích xuất nội dung từ file PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    extracted_text = ""
    for page in pdf_reader.pages:
        text = page.extract_text()
        if text:
            extracted_text += text
    return extracted_text


def get_all_pdf_text(directory):
    all_text = ""
    if os.path.exists(directory):
        for file_name in os.listdir(directory):
            if file_name.endswith(".pdf"):
                pdf_path = os.path.join(directory, file_name)
                print(f"Đang xử lý: {pdf_path}")
                all_text += extract_text_from_pdf(pdf_path)
    else:
        print("Thư mục không tồn tại.")
    return all_text


# Chia văn bản thành các đoạn nhỏ
def split_text_into_chunks(text, chunk_size=1000):
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])
    return chunks


# Tạo embeddings cho các đoạn văn bản và tìm đoạn liên quan bằng FAISS
def find_relevant_chunks(question, chunks, model, top_n=3):
    # Tạo embeddings
    chunk_embeddings = model.encode(chunks)
    question_embedding = model.encode([question])

    # Xây dựng FAISS index
    dimension = chunk_embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(chunk_embeddings)

    # Tìm kiếm top N đoạn liên quan
    _, top_indices = index.search(question_embedding, top_n)
    relevant_chunks = [chunks[i] for i in top_indices[0]]
    return relevant_chunks


# Hỏi mô hình Gemini với ngữ cảnh
# def ask_gemini(question, context=None, history=None):
#     history_text = ""
#     if history:
#         for q, a in history:
#             history_text += f"Q: {q}\nA: {a}\n"
#
#     prompt = f"""
#     You are a helpful assistant. Answer the question based on the provided context and conversation history.
#     If the context does not contain the information needed to answer the question, say "I don't know."
#
#     Conversation History:
#     {history_text}
#
#     Context: {context}
#
#     Question: {question}
#     """
#     response = model.generate_content(prompt)
#     return response.text


def asking(question, context=None, history=None):
    history_text = ""
    if history:
        for q, a in history:
            history_text += f"Q: {q}\nA: {a}\n"

    prompt = f"""
    You are a helpful assistant. Answer the question based on the provided context and conversation history. Sometimes, 
        the context does not contain the information needed to answer the question,
         just answer as naturally as possible with your knowledge.

    Conversation History:
    {history_text}

    Context: {context}
    
    Question: {question}
    """
    response = model.generate_content(prompt)
    return response.text
