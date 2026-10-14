import streamlit as st
import google.generativeai as genai
from docx import Document
import json
from datetime import datetime
from streamlit_mic_recorder import mic_recorder
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Cấu hình giao diện ứng dụng
st.set_page_config(page_title="Ôn tập Vật lý 12 - AI Pro", layout="centered")

# Cấu hình API Gemini (Thầy/cô thay mã API thật vào trong ngoặc kép hoặc dùng st.secrets)
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-3.5-flash-lite')

# Khởi tạo Session State lưu ma trận và trạng thái hệ thống
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
st.write("Ứng dụng tương tác thông minh hỗ trợ học sinh ôn tập bám sát ma trận đặc tả.")

# Sidebar đăng ký thông tin học sinh
st.sidebar.header("👤 Thông tin học sinh")
name = st.sidebar.text_input("Họ và tên:")
cl = st.sidebar.text_input("Lớp:")

if not name or not cl:
    st.warning("⚠️ Thầy/cô và các em học sinh vui lòng nhập Họ tên và Lớp ở thanh bên trái để bắt đầu!")
    st.stop()

st.success(f"Chào em **{name}** - Lớp **{cl}**! Chúc em ôn tập thật tốt.")

# Tạo các Tab chức năng chính
tab1, tab2, tab3 = st.tabs(["📂 1. Chọn Kỳ Thi & Ma Trận", "📝 2. Làm Bài & Tương Tác AI", "📊 3. Lịch Sử & Tiến Bộ"])

with tab1:
    st.subheader("Bước 1: Chọn kỳ thi cần ôn tập")
    exam_type = st.selectbox(
        "Kỳ thi:",
        ["-- Chọn kỳ thi --", "Kiểm tra Giữa kỳ 1", "Kiểm tra Cuối kỳ 1", "Kiểm tra Giữa kỳ 2", "Kiểm tra Cuối kỳ 2"]
    )
    
    st.divider()
    st.subheader("🔒 Khu vực Quản trị Giáo viên (Cấu hình Ma trận)")
    teacher_pass = st.text_input("Nhập mật mã giáo viên để cấu hình:", type="password")
    
    if teacher_pass == "vatly123": # Mật mã giáo viên
        st.success("✅ Xác thực quyền Giáo viên thành công!")
        target_exam = st.selectbox("Chọn kỳ thi cập nhật ma trận:", ["Kiểm tra Giữa kỳ 1", "Kiểm tra Cuối kỳ 1", "Kiểm tra Giữa kỳ 2", "Kiểm tra Cuối kỳ 2"])
        
        current_text = st.session_state['matrices_dict'][target_exam]
        if current_text or st.session_state['matrix_parts'][target_exam] is not None:
            if st.button(f"🗑️ Xóa ma trận hiện tại của {target_exam}", key=f"del_{target_exam}"):
                st.session_state['matrices_dict'][target_exam] = ""
                st.session_state['matrix_parts'][target_exam] = None
                st.success(f"Đã xóa ma trận của {target_exam} thành công!")
                st.rerun()
        
        up_file = st.file_uploader(f"Tải file ma trận cho {target_exam} (.txt, .docx, .pdf, ảnh):", type=["txt", "docx", "pdf", "png", "jpg"], key=f"up_{target_exam}")
        matrix_input = st.text_area("Hoặc dán nội dung ma trận đặc tả:", value=current_text if not current_text.startswith("File") else "", key=f"txt_{target_exam}")
        
        if st.button("💾 Lưu ma trận vào hệ thống", key=f"save_{target_exam}"):
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
            st.success(f"Đã lưu thành công ma trận cho **{target_exam}**!")
            
    elif teacher_pass:
        st.error("❌ Sai mật mã giáo viên!")
        
    if exam_type != "-- Chọn kỳ thi --":
        st.session_state['selected_exam'] = exam_type
        st.info(f"Đã chọn kỳ thi: **{exam_type}**. Vui lòng chuyển sang **Tab 2** để làm bài!")

with tab2:
    current_exam = st.session_state.get('selected_exam', '-- Chọn kỳ thi --')
    if current_exam == '-- Chọn kỳ thi --':
        st.warning("⚠️ Em chưa chọn kỳ thi ở Tab 1! Vui lòng quay lại Tab 1 để chọn kỳ thi trước.")
    else:
        st.write(f"Đang ôn tập cho kỳ thi: **{current_exam}**")
        section = st.radio(
            "Chọn hình thức ôn tập:",
            [
                "Phần I - Trắc nghiệm nhiều lựa chọn (16 câu)",
                "Phần II – Trắc nghiệm đúng sai (3 câu)",
                "Phần III – Trắc nghiệm trả lời ngắn (6 câu)",
                "Toàn bộ đề kiểm tra (Đầy đủ 3 phần)"
            ]
        )
        
        if st.button("🚀 Bắt đầu tạo đề tương tác bám sát ma trận"):
            with st.spinner("🤖 AI đang phân tích ma trận và biên soạn đề thi chuẩn hóa..."):
                active_matrix = st.session_state['matrices_dict'].get(current_exam, "")
                prompt = f"""
                Bạn là chuyên gia ra đề Vật lý 12. Dựa vào ma trận đặc tả sau: {active_matrix}, hãy tạo các câu hỏi ôn tập cho phần '{section}'.
                BẮT BUỘC trả về kết quả dưới dạng một chuỗi JSON thuần túy (không kèm định dạng markdown hay ```json), bao gồm một danh sách các câu hỏi theo cấu trúc chuẩn sau:
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
                    # Reset lại phiên chat mới khi có đề thi mới
                    if 'chat_session' in st.session_state:
                        del st.session_state['chat_session']
                    if 'messages' in st.session_state:
                        del st.session_state['messages']
                except:
                    st.error("AI đang bận hoặc định dạng phản hồi chưa khớp, vui lòng bấm tạo lại đề giúp em nhé!")
                    st.session_state['quiz_data'] = []

        # Hiển thị phần làm bài tương tác nếu đã có dữ liệu đề
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

                # Tự động lưu kết quả vào Google Sheets
                try:
                    scope = ["[https://spreadsheets.google.com/feeds](https://spreadsheets.google.com/feeds)", "[https://www.googleapis.com/auth/drive](https://www.googleapis.com/auth/drive)"]
                    creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
                    client = gspread.authorize(creds)
                    sheet = client.open("LichSuOnTapVatLy12").sheet1
                    
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    row_data = [now_str, name, cl, current_exam, section, final_score]
                    sheet.append_row(row_data)
                    st.balloons()
                    st.toast("✅ Đã tự động lưu kết quả vào hệ thống của giáo viên!", icon="📊")
                except Exception as e:
                    st.warning(f"⚠️ Lưu ý: Chưa kết nối thành công file Google Sheets, nhưng bài làm đã được chấm xong! Chi tiết: {e}")

            # --- CỬA SỔ CHAT ĐA LƯỢT (HỎI - ĐÁP LIÊN TỤC KHÔNG GIỚI HẠN) ---
            st.markdown("---")
            st.subheader("💬 Góc thắc mắc cùng AI (Hỏi - Đáp liên tục)")
            st.markdown("_Em có thể hỏi nhiều lần về bất kỳ câu nào trong đề. AI sẽ luôn nhớ ngữ cảnh để giải đáp cho em!_")
            
            if 'chat_session' not in st.session_state:
                initial_context = f"Đây là đề thi Vật lý 12 học sinh vừa làm: {str(st.session_state.get('quiz_data', ''))}. Hãy đóng vai trò gia sư Vật lý thân thiện, kiên nhẫn giải đáp mọi thắc mắc liên tục cho học sinh."
                st.session_state['chat_session'] = model.start_chat(history=[
                    {"role": "user", "parts": [initial_context]},
                    {"role": "model", "parts": ["Em chào thầy/cô/AI, em đã nắm được đề thi và sẵn sàng giải đáp thắc mắc cho học sinh ạ!"]}
                ])

            if 'messages' not in st.session_state:
                st.session_state['messages'] = []

            for message in st.session_state['messages']:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            col_mic, col_text = st.columns([1, 2])
            audio_text_result = ""
            
            with col_mic:
                audio_info = mic_recorder(start_prompt="🎙️ Thu âm câu hỏi", stop_prompt="⏹️ Dừng", key='recorder_chat_pro')
            
            if audio_info is not None:
                audio_bytes = audio_info.get('bytes')
                if audio_bytes:
                    with st.spinner("🔄 Đang chuyển giọng nói thành văn bản..."):
                        try:
                            audio_prompt = [
                                "Hãy chuyển đổi chính xác đoạn ghi âm giọng nói của học sinh thành văn bản tiếng Việt để hỏi về Vật lý:",
                                {"mime_type": "audio/wav", "data": audio_bytes}
                            ]
                            transcribe_response = model.generate_content(audio_prompt)
                            audio_text_result = transcribe_response.text.strip()
                        except:
                            audio_text_result = ""
            
            with col_text:
                recognized_input = st.text_input("Nội dung giọng nói thu được:", value=audio_text_result, key="rec_input_box_v2")

            user_prompt = st.chat_input("Nhập câu hỏi thắc mắc của em tại đây...")
            target_query = user_prompt if user_prompt else recognized_input
            
            if target_query and target_query != "Nội dung giọng nói thu được từ micro...":
                st.session_state['messages'].append({"role": "user", "content": target_query})
                with st.chat_message("user"):
                    st.markdown(target_query)
                
                with st.chat_message("assistant"):
                    with st.spinner("🤖 AI đang suy nghĩ và giải đáp..."):
                        try:
                            chat_response = st.session_state['chat_session'].send_message(target_query)
                            ai_reply = chat_response.text
                            st.markdown(ai_reply)
                            st.session_state['messages'].append({"role": "assistant", "content": ai_reply})
                        except Exception as e:
                            st.error(f"Đã xảy ra lỗi khi trò chuyện với AI: {e}")

with tab3:
    st.subheader("📊 Theo dõi và đánh giá sự tiến bộ")
    role = st.radio("Bạn là ai?", ["Học sinh", "Giáo viên"])
    if role == "Học sinh":
        st.info(f"Lịch sử ôn tập của học sinh: **{name} ({cl})**. Hệ thống ghi nhận mọi nỗ lực học tập của em qua các lần làm bài.")
    else:
        pwd = st.text_input("Nhập mật mã quản trị giáo viên:", type="password", key="p_hist_admin")
        if pwd == "vatly123":
            st.success("✅ Đăng nhập quyền Giáo viên thành công!")
            st.write("📋 **Bảng tổng hợp lịch sử luyện tập thực tế từ Google Sheets:**")
            
            try:
                scope = ["[https://spreadsheets.google.com/feeds](https://spreadsheets.google.com/feeds)", "[https://www.googleapis.com/auth/drive](https://www.googleapis.com/auth/drive)"]
                creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
                client = gspread.authorize(creds)
                sheet = client.open("LichSuOnTapVatLy12").sheet1
                data = sheet.get_all_records()
                
                if data:
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("Chưa có học sinh nào nộp bài trên hệ thống.")
            except Exception as e:
                st.error(f"Không thể tải dữ liệu từ Google Sheets. Vui lòng kiểm tra lại file credentials.json. Chi tiết lỗi: {e}")
                
        elif pwd:
            st.error("❌ Sai mật mã giáo viên!")
