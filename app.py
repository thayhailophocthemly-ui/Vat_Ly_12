import streamlit as st
import google.generativeai as genai
import docx
import json
from datetime import datetime
from streamlit_mic_recorder import mic_recorder
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Cấu hình giao diện
st.set_page_config(page_title="Ôn tập Vật lý 12 - AI Pro", layout="centered")

# Cấu hình API Gemini
API_KEY = "AQ.Ab8RN6KOM_23kctvGmqvoYAvRuoSzpHiKHEd1nU6IJcL8cmJtw"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Khởi tạo Session State
if 'matrices_dict' not in st.session_state:
    st.session_state['matrices_dict'] = {
        "Kiểm tra Giữa kỳ 1": "",
        "Kiểm tra Cuối kỳ 1": "",
        "Kiểm tra Giữa kỳ 2": "",
        "Kiểm tra Cuối kỳ 2": ""
    }

if 'matrix_parts' not in st.session_state:
    st.session_state['matrix_parts'] = {
        "Kiểm tra Giữa kỳ 1": None,
        "Kiểm tra Cuối kỳ 1": None,
        "Kiểm tra Giữa kỳ 2": None,
        "Kiểm tra Cuối kỳ 2": None
    }

st.title("⚡ HỆ THỐNG ÔN TẬP VẬT LÝ 12 THÔNG MINH")
st.write("Ứng dụng tương tác thông minh bám sát ma trận chuẩn định hướng mới.")

# Sidebar đăng ký thông tin học sinh
st.sidebar.header("👤 Thông tin học sinh")
name = st.sidebar.text_input("Họ và tên:")
cl = st.sidebar.text_input("Lớp:")

if not name or not cl:
    st.warning("⚠️ Vui lòng nhập Họ tên và Lớp ở thanh bên trái để bắt đầu ôn tập!")
    st.stop()

st.success(f"Chào em **{name}** - Lớp **{cl}**! Chúc em ôn tập đạt kết quả cao.")

# Tạo Tab chính
tab1, tab2, tab3 = st.tabs(["📂 1. Chọn Kỳ Thi & Ma Trận", "📝 2. Làm Bài & Tương Tác AI", "📊 3. Lịch Sử & Tiến Bộ"])

with tab1:
    st.subheader("Bước 1: Chọn kỳ thi cần ôn tập")
    exam_type = st.selectbox(
        "Kỳ thi:",
        ["-- Chọn kỳ thi --", "Kiểm tra Giữa kỳ 1", "Kiểm tra Cuối kỳ 1", "Kiểm tra Giữa kỳ 2", "Kiểm tra Cuối kỳ 2"]
    )
    
    st.divider()
    st.subheader("🔒 Khu vực Giáo viên (Cấu hình Ma trận)")
    teacher_pass = st.text_input("Mật mã giáo viên:", type="password")
    
    if teacher_pass == "vatly@123":
        st.success("✅ Xác thực quyền Giáo viên thành công!")
        target_exam = st.selectbox("Chọn kỳ thi cập nhật ma trận:", ["Kiểm tra Giữa kỳ 1", "Kiểm tra Cuối kỳ 1", "Kiểm tra Giữa kỳ 2", "Kiểm tra Cuối kỳ 2"])
        
        current_text = st.session_state['matrices_dict'][target_exam]
        if current_text or st.session_state['matrix_parts'][target_exam] is not None:
            if st.button(f"🗑️ Xóa ma trận hiện tại của {target_exam}"):
                st.session_state['matrices_dict'][target_exam] = ""
                st.session_state['matrix_parts'][target_exam] = None
                st.success("Đã xóa ma trận thành công!")
                st.rerun()
        
        up_file = st.file_uploader(f"Tải file ma trận cho {target_exam} (.txt, .docx, .pdf, ảnh):", type=["txt", "docx", "pdf", "png", "jpg"])
        matrix_input = st.text_area("Hoặc dán nội dung ma trận:", value=current_text if not current_text.startswith("File") else "")
        
        if st.button("💾 Lưu ma trận"):
            extracted = matrix_input
            f_part = None
            if up_file is not None:
                ext = up_file.name.split('.')[-1].lower()
                if ext == "txt":
                    extracted = up_file.read().decode("utf-8")
                elif ext == "docx":
                    doc = docx.Document(up_file)
                    extracted = "\n".join([p.text for p in doc.paragraphs])
                elif ext in ["pdf", "png", "jpg"]:
                    f_bytes = up_file.read()
                    mime = "application/pdf" if ext == "pdf" else f"image/{ext}"
                    f_part = {"mime_type": mime, "data": f_bytes}
                    extracted = f"[File đính kèm: {up_file.name}]"
            
            st.session_state['matrices_dict'][target_exam] = extracted
            st.session_state['matrix_parts'][target_exam] = f_part
            st.success(f"Đã lưu ma trận cho {target_exam} thành công!")
            
    elif teacher_pass:
        st.error("Sai mật mã!")
        
    if exam_type != "-- Chọn kỳ thi --":
        st.session_state['selected_exam'] = exam_type
        st.info(f"Đã chọn: **{exam_type}**. Chuyển sang **Tab 2** để làm bài!")

with tab2:
    current_exam = st.session_state.get('selected_exam', '-- Chọn kỳ thi --')
    if current_exam == '-- Chọn kỳ thi --':
        st.warning("⚠️ Em chưa chọn kỳ thi ở Tab 1!")
    else:
        st.write(f"Đang ôn tập: **{current_exam}**")
        section = st.radio(
            "Chọn hình thức ôn tập:",
            [
                "Phần I - Trắc nghiệm nhiều lựa chọn (16 câu)",
                "Phần II – Trắc nghiệm đúng sai (3 câu)",
                "Phần III – Trắc nghiệm trả lời ngắn (6 câu)",
                "Toàn bộ đề kiểm tra (Đầy đủ 3 phần)"
            ]
        )
        
        if st.button("🚀 Bắt đầu tạo đề tương tác"):
            with st.spinner("🤖 AI đang sinh đề kiểm tra chuẩn hóa cấu trúc..."):
                active_matrix = st.session_state['matrices_dict'].get(current_exam, "")
                prompt = f"""
                Bạn là chuyên gia ra đề Vật lý 12. Dựa vào ma trận: {active_matrix}, hãy tạo các câu hỏi ôn tập cho phần '{section}'.
                BẮT BUỘC trả về kết quả dưới dạng một chuỗi JSON thuần túy (không kèm định dạng markdown nào khác như ```json), bao gồm một danh sách các câu hỏi theo cấu trúc sau:
                [
                  {{
                    "id": 1,
                    "question": "Nội dung câu hỏi...",
                    "options": ["A. Đáp án 1", "B. Đáp án 2", "C. Đáp án 3", "D. Đáp án 4"],
                    "answer": "A",
                    "explanation": "Hướng dẫn giải chi tiết..."
                  }}
                ]
                """
                response = model.generate_content(prompt)
                try:
                    clean_text = response.text.strip().replace("```json", "").replace("```", "")
                    st.session_state['quiz_data'] = json.loads(clean_text)
                except:
                    st.error("AI đang bận, vui lòng bấm tạo lại đề giúp em nhé!")
                    st.session_state['quiz_data'] = []

        if 'quiz_data' in st.session_state and st.session_state['quiz_data']:
            user_answers = {}
            for idx, q in enumerate(st.session_state['quiz_data']):
                st.markdown(f"**Câu {q.get('id', idx+1)}:** {q.get('question')}")
                user_answers[idx] = st.radio(f"Chọn đáp án câu {idx+1}:", q.get('options'), key=f"q_{idx}")
                st.divider()
                
            if st.button("📌 Nộp bài và Xem kết quả"):
                score = 0
                total = len(st.session_state['quiz_data'])
                for idx, q in enumerate(st.session_state['quiz_data']):
                    chosen = user_answers[idx]
                    if chosen and chosen.startswith(q.get('answer')):
                        score += 1
                
                final_score = round((score / total) * 10, 2)
                st.success(f"🎉 Em đã hoàn thành bài! Điểm số đạt được: **{final_score} / 10 điểm** ({score}/{total} câu đúng).")
                
                # Hiển thị giải thích chi tiết
                st.markdown("### 🔍 Hướng dẫn giải chi tiết từng câu:")
                for idx, q in enumerate(st.session_state['quiz_data']):
                    st.write(f"**Câu {idx+1}:** Đáp án đúng là **{q.get('answer')}**. Giải thích: {q.get('explanation')}")

                # --- ĐOẠN KẾT NỐI GOOGLE SHEETS TỰ ĐỘNG LƯU ---
                try:
                    scope = ["[https://spreadsheets.google.com/feeds](https://spreadsheets.google.com/feeds)", "[https://www.googleapis.com/auth/drive](https://www.googleapis.com/auth/drive)"]
                    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
                    client = gspread.authorize(creds)
                    
                    # Mở file Google Sheets tên là LichSuOnTapVatLy12
                    sheet = client.open("LichSuOnTapVatLy12").sheet1
                    
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    row_data = [now_str, name, cl, current_exam, section, final_score]
                    sheet.append_row(row_data)
                    st.balloons()
                    st.toast("✅ Đã tự động lưu kết quả vào hệ thống của giáo viên!", icon="📊")
                except Exception as e:
                    st.warning("⚠️ Lưu ý: Chưa kết nối thành công file Google Sheets, nhưng bài làm đã được chấm xong!")

            # Cửa sổ chat thắc mắc kết hợp Thu âm giọng nói
            st.markdown("---")
            st.subheader("💬 Góc thắc mắc với AI (Hỗ trợ Gõ chữ & Thu âm)")
            audio_info = mic_recorder(start_prompt="🎙️ Bấm để thu âm câu hỏi", stop_prompt="⏹️ Dừng thu âm", key='recorder')
            user_q = st.text_input("Hoặc gõ câu hỏi thắc mắc của em tại đây:")
            
            if user_q:
                ans = model.generate_content(f"Giải đáp thắc mắc môn Vật lý cho học sinh lớp 12: {user_q}")
                st.info(f"🤖 **AI giải đáp:** {ans.text}")
            elif audio_info:
                st.success("Đã ghi nhận giọng nói của em! AI đang phân tích...")
                ans = model.generate_content("Học sinh vừa đặt câu hỏi bằng giọng nói về phần lý thuyết Vật lý 12, hãy giải đáp thật chi tiết và khích lệ học sinh.")
                st.info(f"🤖 **AI giải đáp:** {ans.text}")

with tab3:
    st.subheader("📊 Theo dõi sự tiến bộ")
    role = st.radio("Bạn là ai?", ["Học sinh", "Giáo viên"])
    if role == "Học sinh":
        st.info(f"Lịch sử ôn tập của học sinh: **{name} ({cl})**. Hệ thống ghi nhận mọi nỗ lực học tập của em.")
    else:
        pwd = st.text_input("Mật mã quản trị giáo viên:", type="password", key="p_hist")
        if pwd == "vatly@123":
            st.success("✅ Đăng nhập quyền Giáo viên thành công!")
            st.write("📋 **Bảng tổng hợp lịch sử luyện tập thực tế từ Google Sheets:**")
            
            # --- ĐOẠN ĐỌC DỮ LIỆU TỪ GOOGLE SHEETS HIỂN THỊ CHO GIÁO VIÊN ---
            try:
                scope = ["[https://spreadsheets.google.com/feeds](https://spreadsheets.google.com/feeds)", "[https://www.googleapis.com/auth/drive](https://www.googleapis.com/auth/drive)"]
                creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
                client = gspread.authorize(creds)
                sheet = client.open("LichSuOnTapVatLy12").sheet1
                data = sheet.get_all_records()
                
                if data:
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("Chưa có học sinh nào nộp bài.")
            except Exception as e:
                st.error(f"Không thể tải dữ liệu từ Google Sheets. Vui lòng kiểm tra lại file credentials.json. Chi tiết lỗi: {e}")
                
        elif pwd:
            st.error("Sai mật mã!")
