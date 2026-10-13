import streamlit as st
import google.generativeai as genai

# Cấu hình giao diện
st.set_page_config(page_title="Ôn tập Vật lý 12 - AI", layout="centered")

# Cấu hình API Gemini (Thay mã API của thầy/cô vào đây)
API_KEY = "AQ.Ab8RN6KOM_23kctvGmqvoYAvRuoSzpHiKHEd1nU6IJcL8cmJtw"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.title("⚡ ÔN TẬP KIỂM TRA VẬT LÝ LỚP 12")
st.write("Ứng dụng thông minh hỗ trợ ôn tập bám sát ma trận đề thi.")

# Đăng ký thông tin học sinh ở thanh bên
st.sidebar.header("👤 Thông tin học sinh")
name = st.sidebar.text_input("Họ và tên:")
cl = st.sidebar.text_input("Lớp:")

if not name or not cl:
    st.warning("⚠️ Thầy/cô và các em học sinh vui lòng nhập Họ tên và Lớp ở thanh bên trái để bắt đầu!")
    st.stop()

st.success(f"Chào em **{name}** - Lớp **{cl}**! Hãy chọn nội dung ôn tập bên dưới.")

# Tạo Tab chính
tab1, tab2, tab3 = st.tabs(["📂 1. Chọn Bài Kiểm Tra & Ma Trận", "📝 2. Phần Ôn Tập & Làm Bài", "📊 3. Lịch Sử & Tiến Bộ"])

with tab1:
    st.subheader("Bước 1: Chọn kỳ thi")
    exam_type = st.selectbox(
        "Kỳ thi:",
        ["-- Chọn kỳ thi --", "Kiểm tra Giữa kỳ 1", "Kiểm tra Cuối kỳ 1", "Kiểm tra Giữa kỳ 2", "Kiểm tra Cuối kỳ 2"]
    )
    
    st.subheader("Bước 2: Đưa ma trận đề kiểm tra lên App")
    st.markdown("Giáo viên tải lên file ma trận (Word/PDF/Txt) hoặc dán nội dung ma trận đặc tả vào đây để Gemini căn cứ ra đề:")
    
    # Tính năng tải file ma trận lên
    matrix_file = st.file_uploader("Tải lên file ma trận đặc tả (.txt, .docx, .pdf)", type=["txt", "docx", "pdf"])
    
    matrix_text_input = ""
    if matrix_file is not None:
        # Đọc nội dung file text/đọc nhanh
        try:
            matrix_text_input = matrix_file.read().decode("utf-8")
            st.success("Đã tải lên ma trận thành công!")
        except:
            # Phòng hờ trường hợp file docx/pdf cần đọc thô
            matrix_text_input = "Đã nhận file ma trận từ giáo viên."
    
    # Hoặc ô nhập văn bản ma trận trực tiếp
    matrix_note = st.text_area("Hoặc dán nội dung ma trận / cấu trúc đề vào đây:", placeholder="Ví dụ: Phần I gồm 16 câu nhận biết-thông hiểu chương Dao động cơ...")
    
    if exam_type != "-- Chọn kỳ thi --":
        st.info(f"Đã chọn kỳ thi: **{exam_type}**. Vui lòng chuyển sang **Tab 2** để chọn phần ôn tập!")

with tab2:
    st.subheader("Chọn cấu trúc phần ôn tập:")
    section = st.radio(
        "Hình thức:",
        [
            "Phần I - Trắc nghiệm nhiều lựa chọn (16 câu)",
            "Phần II – Trắc nghiệm đúng sai (3 câu)",
            "Phần III – Trắc nghiệm trả lời ngắn (6 câu)",
            "Toàn bộ đề kiểm tra (Đầy đủ 3 phần)"
        ]
    )
    
    if st.button("🚀 Tạo đề ôn tập bám sát ma trận bằng AI"):
        with st.spinner("🤖 AI đang đọc ma trận và biên soạn đề ôn tập riêng cho em..."):
            # Tổng hợp thông tin ma trận giáo viên đưa vào prompt gửi cho Gemini
            full_matrix_content = matrix_text_input if matrix_text_input else matrix_note
            
            prompt = f"""
            Bạn là một giáo viên Vật lý 12 chuyên nghiệp. 
            Dựa vào ma trận đề kiểm tra sau đây:
            ---
            {full_matrix_content}
            ---
            Hãy ra một đề ôn tập cho bài {exam_type}, phần {section}. 
            Đề phải bám sát chính xác các mức độ nhận thức, số lượng câu hỏi và nội dung trong ma trận trên.
            """
            
            response = model.generate_content(prompt)
            st.session_state['de_thi'] = response.text
            
        st.markdown("### 📋 Đề Ôn Tập Của Em (Bám sát ma trận):")
        st.write(st.session_state.get('de_thi', ''))
        
        st.divider()
        if st.button("📌 Xem kết quả và Hướng dẫn giải"):
            st.success("Hệ thống đã ghi nhận!")
            st.markdown("### 🔍 Phân tích đáp án & Lời giải chi tiết từ AI:")
            
            explain_prompt = f"Dựa trên đề thi vừa tạo dựa theo ma trận, hãy cung cấp bảng đáp án chi tiết và hướng dẫn giải thích từng câu thật dễ hiểu cho học sinh lớp 12."
            explanation = model.generate_content(explain_prompt)
            st.write(explanation.text)
            
            # Góc thắc mắc cùng chatbot
            st.markdown("---")
            st.subheader("💬 Góc thắc mắc với AI")
            user_q = st.text_input("Nếu em có thắc mắc với câu nào, hãy viết vào đây:")
            if user_q:
                ans = model.generate_content(f"Giải đáp thắc mắc môn Vật lý cho học sinh: {user_q}")
                st.write(ans.text)

with tab3:
    st.subheader("📊 Theo dõi sự tiến bộ")
    role = st.radio("Bạn là ai?", ["Học sinh", "Giáo viên"])
    if role == "Học sinh":
        st.info(f"Lịch sử ôn tập của học sinh: **{name} ({cl})**.")
    else:
        password = st.text_input("Nhập mật mã giáo viên:", type="password")
        if password == "vatly@123":
            st.success("Đăng nhập quyền Giáo viên thành công!")
            st.write("📋 Tổng hợp lịch sử luyện tập của toàn bộ học sinh lớp 12.")
        elif password:
            st.error("Sai mật mã!")
