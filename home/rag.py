import PyPDF2
import faiss
import google.generativeai as genai
import os
import googleapiclient.discovery

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





# Hàm tìm kiếm trên web (Google Custom Search API)
def search_web(query):
    # Cấu hình API Key và CSE (Custom Search Engine ID)
    api_key = "AIzaSyBUYhrlVD7STFwU0tLMNifT-w_LUTf6FNY"
    cse_id = "1314150afea604498"

    service = googleapiclient.discovery.build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=query, cx=cse_id).execute()
    return res['items']  # Danh sách kết quả tìm kiếm


# Hàm trả lời câu hỏi dựa trên lịch sử hội thoại và context
def asking(question, context=None, history=None):
    history_text = ""
    if history:
        for q, a in history:
            history_text += f"Q: {q}\nA: {a}\n"

    # Tạo prompt cho AI
    prompt = f"""
    You are a helpful assistant. Answer the question based on the provided context and conversation history. 
    Sometimes, the context does not contain the information needed to answer the question, 
    just answer as naturally as possible with your knowledge. 
    If your knowledge is not enough to answer the question, say: "hmm"
    search the internet for the most relevant information and use that to provide an accurate response.

    Conversation History:
    {history_text}

    Context: {context}

    Question: {question}
    """

    # Nếu AI không thể trả lời câu hỏi, thực hiện tìm kiếm trên web
    if "hmm" in model.generate_content(prompt):  # Kiểm tra nếu AI không biết câu trả lời
        search_results = search_web(question)
        # Trích xuất thông tin từ kết quả tìm kiếm
        result_snippet = search_results[0]['snippet'] if search_results else "I couldn't find relevant information."
        response_text = f"Search result: {result_snippet}"
    else:
        # Nếu AI có thể trả lời, trả về câu trả lời từ model
        response_text = model.generate_content(prompt).text

    return response_text


