    import streamlit as st
import google.generativeai as genai

# Cấu hình giao diện
st.set_page_config(page_title="Ôn tập Vật lý 12 - AI", layout="centered")

# Cấu hình API Gemini (Thay mã API của thầy/cô vào đây)
API_KEY = "AQ.Ab8RN6KOM_23kctvGmqvoYAvRuoSzpHiKHEd1nU6IJcL8cmJtw"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Khởi tạo kho lưu trữ ma trận và đề thi trong phiên làm việc
if 'matrices_dict' not in st.session_state:
    st.session_state['matrices_dict'] = {
        "Kiểm tra Giữa kỳ 1": "",
        "Kiểm tra Cuối kỳ 1": "",
        "Kiểm tra Giữa kỳ 2": "",
        "Kiểm tra Cuối kỳ 2": ""
    }

st.title("⚡ HỆ THỐNG ÔN TẬP VẬT LÝ 12 THÔNG MINH")
st.write("Ứng dụng hỗ trợ ôn tập bám sát ma trận chuẩn định hướng kiểm tra đánh giá.")

# Đăng ký thông tin học sinh ở thanh bên
st.sidebar.header("👤 Thông tin học sinh")
name = st.sidebar.text_input("Họ và tên:")
cl = st.sidebar.text_input("Lớp:")

if not name or not cl:
    st.warning("⚠️ Thầy/cô và các em học sinh vui lòng nhập Họ tên và Lớp ở thanh bên trái để bắt đầu!")
    st.stop()

st.success(f"Chào em **{name}** - Lớp **{cl}**! Hãy chọn nội dung ôn tập bên dưới.")

# Tạo Tab chính
tab1, tab2, tab3 = st.tabs(["📂 1. Chọn Kỳ Thi & Cấu Hình Ma Trận", "📝 2. Phần Ôn Tập & Làm Bài", "📊 3. Lịch Sử & Tiến Bộ"])

with tab1:
    st.subheader("Bước 1: Chọn kỳ thi cần ôn tập")
    exam_type = st.selectbox(
        "Kỳ thi:",
        ["-- Chọn kỳ thi --", "Kiểm tra Giữa kỳ 1", "Kiểm tra Cuối kỳ 1", "Kiểm tra Giữa kỳ 2", "Kiểm tra Cuối kỳ 2"]
    )
    
    st.divider()
    st.subheader("🔒 Khu vực dành cho Giáo viên (Cấu hình Ma trận)")
    teacher_pass = st.text_input("Nhập mật mã giáo viên để cấu hình/thay đổi ma trận:", type="password")
    
    if teacher_pass == "vatly@123": # Mật mã giáo viên (Thầy/cô có thể đổi tùy ý ở đây)
        st.success("✅ Đã xác thực quyền Giáo viên thành công!")
        
        target_exam = st.selectbox(
            "Chọn kỳ thi muốn cập nhật ma trận:",
            ["Kiểm tra Giữa kỳ 1", "Kiểm tra Cuối kỳ 1", "Kiểm tra Giữa kỳ 2", "Kiểm tra Cuối kỳ 2"]
        )
        
        current_matrix = st.session_state['matrices_dict'][target_exam]
        
        if current_matrix:
            st.info(f"📌 Đang có sẵn ma trận cho: **{target_exam}**")
            if st.button(f"🗑️ Xóa ma trận hiện tại của {target_exam}"):
                st.session_state['matrices_dict'][target_exam] = ""
                st.success(f"Đã xóa ma trận của {target_exam} thành công! Thầy/cô có thể tải ma trận mới lên.")
                st.rerun()
        
        # Ô tải file hoặc dán ma trận
        up_file = st.file_uploader(f"Tải lên file ma trận cho {target_exam} (.txt)", type=["txt"])
        matrix_input = st.text_area(f"Hoặc dán nội dung ma trận đặc tả cho {target_exam}:", value=current_matrix if not current_matrix.startswith("File") else "")
        
        if st.button("💾 Lưu ma trận này vào hệ thống"):
            final_content = matrix_input
            if up_file is not None:
                try:
                    final_content = up_file.read().decode("utf-8")
                except:
                    final_content = "Đã nhận file ma trận tải lên."
            
            st.session_state['matrices_dict'][target_exam] = final_content
            st.success(f"Đã lưu thành công ma trận cho **{target_exam}**! Gemini sẽ bám sát ma trận này để ra đề.")
            
    elif teacher_pass:
        st.error("❌ Sai mật mã giáo viên! Học sinh không thể thay đổi ma trận.")
    
    # Lưu lựa chọn kỳ thi của học sinh vào phiên làm việc
    if exam_type != "-- Chọn kỳ thi --":
        st.session_state['selected_exam'] = exam_type
        st.info(f"Đã chọn kỳ thi: **{exam_type}**. Vui lòng chuyển sang **Tab 2** để chọn phần ôn tập!")

with tab2:
    current_exam_chosen = st.session_state.get('selected_exam', '-- Chọn kỳ thi --')
    if current_exam_chosen == '-- Chọn kỳ thi --':
        st.warning("⚠️ Em chưa chọn kỳ thi ở Tab 1! Vui lòng quay lại Tab 1 để chọn kỳ thi trước.")
    else:
        st.write(f"Đang ôn tập cho: **{current_exam_chosen}**")
        
        # Kiểm tra xem kỳ này đã có ma trận chưa
        active_matrix = st.session_state['matrices_dict'].get(current_exam_chosen, "")
        if not active_matrix:
            st.warning(f"⚠️ Lưu ý: Giáo viên chưa cập nhật ma trận cho kỳ **{current_exam_chosen}**. Gemini sẽ ra đề theo chuẩn chung của Bộ GD&ĐT.")
        
        section = st.radio(
            "Chọn hình thức ôn tập:",
            [
                "Phần I - Trắc nghiệm nhiều lựa chọn (16 câu)",
                "Phần II – Trắc nghiệm đúng sai (3 câu)",
                "Phần III – Trắc nghiệm trả lời ngắn (6 câu)",
                "Toàn bộ đề kiểm tra (Đầy đủ 3 phần)"
            ]
        )
        
        if st.button("🚀 Tạo đề ôn tập bám sát ma trận bằng AI"):
            with st.spinner("🤖 AI đang đọc ma trận riêng của kỳ thi này và biên soạn đề..."):
                prompt = f"""
                Bạn là một giáo viên Vật lý 12 chuyên nghiệp.
                Đây là ma trận đặc tả dành riêng cho bài {current_exam_chosen}:
                ---
                {active_matrix if active_matrix else "Ma trận tiêu chuẩn Vật lý 12 định hướng mới"}
                ---
                Hãy ra một đề ôn tập cho phần {section}. 
                Đề phải bám sát chính xác các mức độ nhận thức, số lượng câu hỏi quy định trong ma trận trên.
                """
                
                response = model.generate_content(prompt)
                st.session_state['de_thi'] = response.text
                
            st.markdown("### 📋 Đề Ôn Tập Của Em:")
            st.write(st.session_state.get('de_thi', ''))
            
            st.divider()
            if st.button("📌 Xem kết quả và Hướng dẫn giải"):
                st.success("Hệ thống đã ghi nhận!")
                st.markdown("### 🔍 Phân tích đáp án & Lời giải chi tiết từ AI:")
                
                explain_prompt = f"Dựa trên đề thi vừa tạo, hãy cung cấp bảng đáp án chi tiết và hướng dẫn giải thích từng câu thật dễ hiểu cho học sinh lớp 12."
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
        password = st.text_input("Nhập mật mã quản trị giáo viên:", type="password", key="teacher_history_pass")
        if password == "vatly@123":
            st.success("Đăng nhập quyền Giáo viên thành công!")
            st.write("📋 Tổng hợp lịch sử luyện tập của toàn bộ học sinh lớp 12.")
        elif password:
            st.error("Sai mật mã!")
