
import streamlit as st
import google.generativeai as genai

# --- إعدادات التطبيق ---
st.set_page_config(page_title="تطبيق صديقي", page_icon="🤖")

# !!!!!!! هام جداً: استبدل النص بين علامات التنصيص بمفتاحك !!!!!!!
my_api_key = "AIzaSyCwQX47rlWYzgKWz0lQK9P0JJUUXQLPSfE..." 

# إعداد الصفحة
st.title("مرحباً بك في التطبيق 👋")
st.write("هذا التطبيق تجربة خاصة لصديقي العزيز")

# تشغيل الذكاء الاصطناعي
try:
    genai.configure(api_key=my_api_key)
    model = genai.GenerativeModel('gemini-pro')

    # حفظ المحادثة
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # عرض الرسائل القديمة
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # استقبال رسالة جديدة
    if prompt := st.chat_input("اكتب سؤالك هنا..."):
        # عرض رسالة المستخدم
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # الحصول على الرد
        try:
            response = model.generate_content(prompt)
            with st.chat_message("assistant"):
                st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error("حدث خطأ في الاتصال، تأكد من النت أو المفتاح.")

except Exception:
    st.error("المفتاح غير صحيح أو مفقود")
  
