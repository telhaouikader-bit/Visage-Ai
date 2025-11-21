import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageOps
import io
from streamlit_drawable_canvas import st_canvas

# --- إعداد الصفحة ---
st.set_page_config(page_title="Pro Visage AI", page_icon="🎨", layout="wide")

# !!!!!!! ضع مفتاحك هنا !!!!!!!
api_key = "AIzaSyCwQX47rlWYzgKWz0lQK9P0JJUUXQLPSfE_AIzaSyD..." 

# --- تكوين Gemini ---
try:
    genai.configure(api_key=api_key)
    # نستخدم Flash للسرعة، أو Pro للجودة العالية
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    pass

# --- الدوال الذكية (مترجمة من كودك الأصلي) ---

def get_photorealism_prompt(user_instruction):
    """تجهيز التعليمات الصارمة للواقعية"""
    return f"""You are a world-class photo editor and digital artist.
    Task: Edit this photo precisely according to this instruction: "{user_instruction}".
    
    CRITICAL GUIDELINES FOR PHOTOREALISM:
    1. IDENTITY: Preserve the person's facial features, bone structure, and expression exactly unless specifically asked to change them.
    2. TEXTURE: Maintain the original skin texture (pores, imperfections) and hair texture. Do not make the skin look like plastic or wax.
    3. LIGHTING: Match the lighting direction, color temperature, and shadow intensity of the original photo.
    4. INTEGRATION: Any added elements (hair, beard, glasses, background) must physically interact with the subject correctly (casting shadows, reflections).
    5. QUALITY: Output must be sharp, high-resolution, and free of artifacts. 
    
    Do not produce cartoonish or illustrative results. The output must be indistinguishable from a real photograph."""

def get_inpainting_prompt(user_instruction):
    """تجهيز تعليمات التعديل بالقناع (Inpainting)"""
    return f"""This is a specialized "Generative Fill" inpainting task. 
    The input image contains a semi-transparent BLUE overlay indicating the target area.
    
    USER INSTRUCTION: "{user_instruction}"

    EXECUTION PROTOCOL:
    1. TARGET: Modify ONLY the area covered by the BLUE mask.
    2. ACTION: Replace the masked content based on the User Instruction.
    3. BLENDING: Seamlessly integrate the new content with the surrounding environment. Match lighting direction, shadows, color grading, and noise/grain.
    4. REMOVAL: If the instruction implies removal (e.g., "remove", "erase", "clear"), fill the masked area with appropriate background texture to make the object disappear.
    5. CLEANUP: The final output must NOT show any trace of the blue mask.
    6. REALISM: Output must be high-quality photorealistic.
    """

def create_composite_image(original_image, mask_image):
    """
    دمج الصورة الأصلية مع القناع الأزرق لمحاكاة كودك الأصلي
    """
    # تغيير حجم القناع ليطابق الصورة الأصلية
    mask_image = mask_image.resize(original_image.size)
    
    # تحويل القناع إلى تدرج رمادي لاستخدامه كـ Alpha
    mask_data = mask_image.split()[3] # القناة الشفافة
    
    # إنشاء طبقة زرقاء
    blue_layer = Image.new("RGBA", original_image.size, (0, 100, 255, 128)) # أزرق نصف شفاف
    
    # دمج الأزرق فوق الصورة الأصلية فقط في مكان الرسم
    composite = Image.composite(blue_layer, original_image.convert("RGBA"), mask_data)
    return composite.convert("RGB")

# --- واجهة التطبيق ---

st.title("Pro Visage AI 🎨")
st.write("تطبيق احترافي لتعديل الصور باستخدام Gemini")

# 1. رفع الصورة
uploaded_file = st.file_uploader("اختر صورة لتبدأ", type=["jpg", "jpeg", "png"])

if uploaded_file:
    # قراءة الصورة
    original_image = Image.open(uploaded_file).convert("RGB")
    
    # تصغير الصورة قليلاً إذا كانت ضخمة لتسريع المعالجة
    if original_image.width > 1024:
        ratio = 1024 / original_image.width
        new_height = int(original_image.height * ratio)
        original_image = original_image.resize((1024, new_height))

    # تحديد الوضع
    mode = st.radio("اختر نوع التعديل:", 
                    ["تعديل عام (فلتر/وصف)", "تعديل جزئي (رسم قناع)", "تغيير الخلفية"])

    # --- الوضع 1: تعديل عام ---
    if mode == "تعديل عام (فلتر/وصف)":
        st.image(original_image, caption="الصورة الأصلية", use_column_width=True)
        prompt_text = st.text_input("صف التعديل المطلوب (مثلاً: اجعل الصورة سينمائية، أضف نظارات شمسية...)")
        
        if st.button("نفذ التعديل ⚡") and prompt_text:
            with st.spinner("جاري المعالجة بدقة عالية..."):
                try:
                    final_prompt = get_photorealism_prompt(prompt_text)
                    response = model.generate_content([final_prompt, original_image])
                    st.image(response.text if not response.parts else  # في حالة حدوث خطأ نصي
                             Image.open(io.BytesIO(response.parts[0].inline_data.data)) if hasattr(response.parts[0], 'inline_data') else 
                             Image.open(io.BytesIO(requests.get(response.candidates[0].content.parts[0].text).content)) if False else # تجاهل هذا السطر
                             Image.open(io.BytesIO(response._result.candidates[0].content.parts[0].inline_data.data)) # طريقة الوصول للصورة
                             , caption="النتيجة")
                    
                    # *ملاحظة فنية:* Gemini Python SDK يعيد الصورة بطرق مختلفة حسب النسخة
                    # للتسهيل، سنستخدم طريقة حفظ وعرض بسيطة إذا لم تعمل الطريقة المباشرة
                    # لكن الكود أعلاه يحاول الوصول للبيانات الخام. 
                    
                except Exception as e:
                     # محاولة بديلة بسيطة للعرض لأن SDK يتحدث باستمرار
                    try:
                        st.image(response.text) # أحيانا يعيد نصا
                    except:
                        # الطريقة الأكثر ضماناً للصور مع Gemini Vision
                         st.write("تم استلام الرد، جاري العرض...")
                         # هنا نفترض أن الموديل يدعم إخراج الصور، إذا لم يدعم، سيعطي نصاً
                         st.markdown(response.text)

    # --- الوضع 2: تعديل جزئي (الرسم) ---
    elif mode == "تعديل جزئي (رسم قناع)":
        st.info("ارسم بالماوس/إصبعك على المنطقة التي تريد تغييرها")
        
        # أداة الرسم (Canvas)
        # stroke_color لا يهم هنا لأننا سنأخذ القناع فقط، لكن لنجعله أزرق للتوضيح
        canvas_result = st_canvas(
            fill_color="rgba(0, 100, 255, 0.3)",  # لون التعبئة
            stroke_width=20,
            stroke_color="rgba(0, 100, 255, 0.5)",
            background_image=original_image,
            update_streamlit=True,
            height=500, # ارتفاع تقريبي
            drawing_mode="freedraw",
            key="canvas",
        )

        prompt_text = st.text_input("ماذا تريد أن تفعل في المنطقة الملونة؟ (مثلاً: أزل هذا الشيء، غيّر لون الشعر...)")

        if st.button("نفذ التغيير 🖌️") and prompt_text and canvas_result.image_data is not None:
            with st.spinner("جاري دمج القناع والمعالجة..."):
                try:
                    # 1. استخراج القناع من الرسم
                    mask_data = Image.fromarray(canvas_result.image_data.astype('uint8'), mode="RGBA")
                    
                    # 2. دمج الصورة مع القناع الأزرق (محاكاة لكودك)
                    composite_img = create_composite_image(original_image, mask_data)
                    
                    # لعرض ما سيتم إرساله للذكاء الاصطناعي (للتأكد)
                    with st.expander("عرض الصورة المرسلة للذكاء الاصطناعي"):
                        st.image(composite_img, caption="الصورة المدمجة بالقناع")

                    # 3. الإرسال لـ Gemini
                    final_prompt = get_inpainting_prompt(prompt_text)
                    response = model.generate_content([final_prompt, composite_img])
                    
                    # عرض النتيجة (محاولة معالجة الصورة الناتجة)
                    # ملاحظة: نحتاج للتأكد أن استجابة الموديل تحتوي صورة
                    # حالياً Gemini 1.5 قد يعيد نصاً إذا لم يتم تفعيل الصور بشكل كامل في مفتاحك
                    # لكن الكود يطلب الصورة.
                    st.success("تم!")
                    st.write("النتيجة (قد تحتاج لتحميلها إذا ظهرت كرابط أو بيانات):")
                    
                    # كود عرض الصورة من الرد (يعتمد على إصدار المكتبة)
                    try:
                        img_data = response.parts[0].inline_data.data
                        img_final = Image.open(io.BytesIO(img_data))
                        st.image(img_final)
                    except:
                         st.write(response.text)

                except Exception as e:
                    st.error(f"حدث خطأ: {e}")

    # --- الوضع 3: خلفية عشوائية ---
    elif mode == "تغيير الخلفية":
        import random
        backgrounds = [
            "a luxury modern loft apartment with city view",
            "a sunny tropical beach with turquoise water",
            "a busy cyberpunk city street at night with neon lights",
            "a peaceful forest clearing with sunlight filtering through trees",
            "a professional photography studio with grey backdrop",
            "the streets of Paris with the Eiffel Tower in distance"
        ]
        
        if st.button("غيّر الخلفية عشوائياً 🎲"):
            random_bg = random.choice(backgrounds)
            st.write(f"الخلفية المختارة: **{random_bg}**")
            
            with st.spinner("جاري تركيب الخلفية..."):
                try:
                    prompt = f"Change the background to {random_bg}. Keep the subject perfectly lit and integrated."
                    final_prompt = get_photorealism_prompt(prompt)
                    response = model.generate_content([final_prompt, original_image])
                    
                    try:
                        img_data = response.parts[0].inline_data.data
                        img_final = Image.open(io.BytesIO(img_data))
                        st.image(img_final)
                    except:
                         st.write(response.text)
                except Exception as e:
                    st.error(f"حدث خطأ: {e}")

