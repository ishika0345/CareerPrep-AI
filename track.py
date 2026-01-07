from dotenv import load_dotenv
load_dotenv()
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.colors import black
from serpapi import GoogleSearch

import streamlit as st
import os
from PIL import Image
from pypdf import PdfReader

import google.generativeai as genai

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_gemini_response(input,pdf_content,prompt):
    model=genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(
    f"""
    Job Description:
    {input}

    Resume:
    {pdf_content}

    Instructions:
    {prompt}
    """
)

    return response.text

def input_pdf_setup(uploaded_file):
    if uploaded_file is not None:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    else:
        raise FileNotFoundError("No file uploaded")
    
def generate_resume_pdf(pdf_content, filename="generated_resume.pdf"):
    file_path = os.path.join(os.getcwd(), filename)

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    base_style = ParagraphStyle(
        name="ResumeStyle",
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        spaceAfter=6,
        textColor=black,
        alignment=TA_LEFT
    )

    story = []

    for line in pdf_content.split("\n"):
        if line.strip().isupper():  # HEADINGS
            heading_style = ParagraphStyle(
                name="HeadingStyle",
                fontName="Helvetica-Bold",
                fontSize=14,
                spaceBefore=12,
                spaceAfter=6
            )
            story.append(Paragraph(line, heading_style))

        elif line.strip().startswith("•"):
            bullet_style = ParagraphStyle(
                name="BulletStyle",
                leftIndent=12,
                bulletIndent=0
            )
            story.append(Paragraph(line, bullet_style))

        else:
            story.append(Paragraph(line, base_style))

    doc.build(story)
    return file_path


def fetch_live_jobs(role, location="India", max_results=10):
    params = {
        "engine": "google_jobs",
        "q": role,
        "location": location,
        "api_key": os.getenv("SERPAPI_KEY")
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    jobs = []

    for job in results.get("jobs_results", [])[:max_results]:
        jobs.append({
            "company": job.get("company_name", "N/A"),
            "title": job.get("title", "N/A"),
            "location": job.get("location", "N/A"),
            "posted": job.get("detected_extensions", {}).get("posted_at", "Recently"),
            "apply_link": (
                job.get("apply_options", [{}])[0].get("link")
                if job.get("apply_options")
                else None
            )
        })

    return jobs

def extract_best_role(pdf_content):
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""
    You are a career expert.

    TASK:
    From the given resume text, identify the BEST-SUITED job role
    the candidate should apply for.

    Resume:
    {pdf_content}

    OUTPUT RULES:
    - Give ONLY ONE role
    - No explanation
    - Example output: Data Analyst Intern
    """

    response = model.generate_content(prompt)
    return response.text.strip()



#streamlit
st.set_page_config(
    page_title="CareerPrep AI",
    page_icon="📄",
    layout="wide"
)

st.header("Resume2Interview :briefcase:")
st.subheader("📌 Job Description")
input_text = st.text_area(
    "Paste the Job Description here",
    height=180,
    placeholder="Enter job requirements, skills, tools, responsibilities..."
)

st.subheader("📄 Upload Resume")
uploaded_file = st.file_uploader(
    "Upload resume in PDF format",
    type=["pdf"]
)

if uploaded_file:
    st.success("✅ Resume uploaded successfully")


with st.sidebar:
    st.title("ℹ️ How it works")
    st.markdown("""
    1. Upload your resume (PDF)  
    2. Paste the Job Description  
    3. Choose an action  
    4. Get ATS-optimized results  
    """)
    st.title("🔍Discover Jobs")
    btn_live_jobs = st.button("🏢 Live Hiring Companies")

def generate_interview_questions(job_description, pdf_content):
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""
You are a senior technical interviewer.

TASK:
Generate interview questions based strictly on the Job Description and the candidate's Resume.

INPUTS:
Job Description:
{job_description}

Resume:
{pdf_content}

INSTRUCTIONS:
- Questions must match the role and required skills
- Difficulty: Beginner to Advanced
- Avoid generic questions
- No explanations, ONLY questions

OUTPUT FORMAT:

TECHNICAL QUESTIONS:
1.
2.
3.
4.
5.

HR / BEHAVIORAL QUESTIONS:
1.
2.
3.

SCENARIO-BASED QUESTIONS:
1.
2.

CODING / CASE STUDY QUESTIONS (if applicable):
1.
2.
"""

    response = model.generate_content(prompt)
    return response.text.strip()




st.subheader("🚀 Actions")
col1, col2, col3, col4 = st.columns(4)

with col1:
     submit1=st.button("🧠 Resume Analysis")
with col2:
     submit2=st.button("📊 JD Match %")
with col3:
     submit3=st.button("✨ Generate JD-Based Resume")
with col4:
    submit4 = st.button("🎯 Interview Questions")     

input_prompt1="""
You are an experienced HR with Tech Experience in the field of Data science,Full Stack Web development,Big Data Engineering,DEVOPS,Data Analyst, Your task is to review the provided resume against the job description for this profiles.
Please share your professional evaluation on whether the candidate's profile aligns with the role. 
Highlight the strengths and weakness of the applicant in relation to the specified job requirements. 
"""

input_prompt2="""
You are an skilled ATS (Applicant Tracking System) scanner with a deep understanding of Data Science, Full Stack Web Development, Big Data Engineering, DevOps, Data Analyst and deep ATS functionality,
your task is to evaluate the resume against the provided job description.
 First the output keywords missing and at last give final thoughts
INSTRUCTIONS:
- Give percentage score (0–100) for each section:
  1. Skills
  2. Work Experience
  3. Projects
  4.Education
- Briefly explain each score.
- Do NOT generate resume.
- every section output should starts with new line.

OUTPUT FORMAT:
Skills: XX% – explanation
Experience: XX% – explanation
Projects: XX% – explanation
Education: XX% – explanation
Overall ATS Score: XX%
Final Thoughts: Summary of resume's fit for the job description.
"""

input_prompt3="""
You are an expert ATS-friendly resume writer and hiring manager.

TASK:
Generate a professional, ATS-optimized resume that is highly aligned with the given Job Description.
Academic details and education MUST be extracted strictly from the uploaded resume PDF content.

INPUTS:
1. Job Description:
{input}

2. Uploaded Resume PDF Text (raw extracted text):
{pdf_content}

INSTRUCTIONS:
- Extract the following ONLY from the uploaded PDF:
  • Education (degree, institution, year, CGPA/percentage if available)
  • Academic achievements
  • Certifications (if present)
- DO NOT invent or modify academic information.
- If academic information is missing in the PDF, omit the section entirely.

- Analyze the Job Description and identify:
  • Required skills
  • Preferred skills
  • Tools & technologies
  • ATS keywords

- Optimize the resume to match the Job Description by:
  • Rewriting experience and project bullet points
  • Aligning skills with JD keywords naturally
  • Using strong action verbs
  • Quantifying impact using numbers and metrics

- Maintain factual correctness:
  • Do NOT fabricate education, certifications, or degrees
  • Projects and experience may be reframed but not invented

FORMAT REQUIREMENTS:
- Resume must be ATS-safe and PDF-ready
- Use clear section headings:
  1. Professional Summary
  2. Education (from PDF only)
  3. Work Experience
  4. Projects
  5. Skills 
  6. Coding Profile (from PDF only)
  7. Achievements
  8. Certifications (from PDF only)
- Use bullet points only
- Avoid tables, icons, graphics, or emojis
- Keep resume length to 1–2 pages

STRICT DESIGN RULES:
- Preserve the SAME:
  • Section order
  • Heading capitalization style
  • Bullet point style
  • Line spacing pattern
  • Overall resume tone
- Do NOT change layout structure
- Do NOT add new sections
- Do NOT invent education or certifications
- After each Heading capitalization style, leave a line space
- Education & academics must come ONLY from uploaded PDF

PROJECT RULES (VERY IMPORTANT):
- Analyze existing projects from the uploaded resume.
- If relevant projects exist:
  • Rewrite and optimize them to match the Job Description.
- If projects are missing OR weakly related:
  • Generate 1 realistic, job-relevant projects.
  • Clearly label them as "Suggested Project" or "Academic Project".
  • Projects must match the Job Description tools, skills, and domain.
  • Projects should be feasible for a student or early professional.

PROJECT FORMAT:
For each project include:
- Project Title
- Short description (1 line)
- Technologies Used
- Key responsibilities / outcomes (2-3 bullet points)
- Measurable impact (where applicable)

FORMAT & STYLE RULES:
- Preserve section order, headings, bullet style, and spacing
  similar to the uploaded resume.
- Do NOT add fake work experience.
- Do NOT add company names for generated projects.
- Resume must be ATS-safe and PDF-ready.


CONTENT RULES:
- Optimize skills, projects, and experience for JD
- Rewrite bullets but KEEP SAME STRUCTURE
- Quantify impact where possible

OUTPUT RULES:
- Output plain text only
- Follow EXACT visual structure of uploaded resume
- No explanations
"""


if submit1:
   if uploaded_file is not None:
        status = st.empty()

        status.info("🔍 Reading uploaded resume...")
        pdf_content = input_pdf_setup(uploaded_file)

        status.info("📊 Analyzing job description...")

        status.info("🧠 Optimizing resume using ATS rules...")
        response = get_gemini_response(input_prompt1, pdf_content, input_text)

        status.success("✅ Analyzed Resume successfully!")
       
        st.subheader("Resume Analysis:")   
        st.write(response) 
   else:
       st.write("Please upload the resume")

elif submit2:
    if uploaded_file is not None:
        status = st.empty()

        status.info("🔍 Reading uploaded resume...")
        pdf_content = input_pdf_setup(uploaded_file)

        status.info("📊 Analyzing job description...")

        status.info("🧠 Optimizing resume using ATS rules...")
        response = get_gemini_response(input_prompt2, pdf_content, input_text)

        status.success("✅ Analyzed Resume successfully!")
        st.subheader("Resume Match Percentage:")   
        st.write(response) 
    else:
         st.write("Please upload the resume")

elif submit3:
    if uploaded_file is not None:
    
        status = st.empty()

        status.info("🔍 Reading uploaded resume...")
        pdf_content = input_pdf_setup(uploaded_file)

        status.info("📊 Analyzing job description...")

        status.info("🧠 Optimizing resume using ATS rules...")
        response = get_gemini_response(input_prompt3, pdf_content, input_text)

        status.success("✅ Resume generated successfully!")


        st.subheader("Generated Resume:")
        st.text(response)

        # Generate PDF
        pdf_file_path = generate_resume_pdf(response)

        # Download button
        with open(pdf_file_path, "rb") as f:
            st.markdown("### 📥 Download Your Resume")

            st.download_button(
            label="⬇️ Download ATS-Optimized Resume (PDF)",
            data=open(pdf_file_path, "rb"),
            file_name="ATS_Resume.pdf",
            mime="application/pdf"
)

    else:
        st.write("Please upload the resume")

        st.markdown("""
<style>
.job-card {
    background-color: #ffffff;
    padding: 14px 16px;
    border-radius: 8px;
    border: 1px solid #e6e6e6;
    margin-bottom: 12px;
}

.job-company {
    font-size: 16px;
    font-weight: 600;
    color: #222;
    margin-bottom: 2px;
}

.job-title {
    font-size: 15px;
    font-weight: 500;
    color: #333;
    margin-bottom: 6px;
}

.job-meta {
    font-size: 13px;
    color: #666;
    margin-bottom: 6px;
}

.job-apply a {
    font-size: 13px;
    color: #1a73e8;
    text-decoration: none;
    font-weight: 500;
    margin-bottom: 12px;
}

.job-apply a:hover {
    text-decoration: underline;
}
</style>
""", unsafe_allow_html=True)


if btn_live_jobs:
    if uploaded_file is not None:
        status = st.empty()

        status.info("📄 Reading resume...")
        pdf_content = input_pdf_setup(uploaded_file)

        status.info("🧠 Finding best-suited role...")
        best_role = extract_best_role(pdf_content)

        status.info(f"🔍 Searching live jobs for: {best_role}")
        jobs = fetch_live_jobs(best_role)

        status.success("✅ Live job openings found!")

        st.subheader(f"🏢 Live Job Openings for: {best_role}")

        if not jobs:
            st.warning("No live jobs found at the moment. Try again later.")
        else:
            for job in jobs:
                st.markdown(f"""
<div class="job-card">
    <div class="job-company">{job['company']}</div>
    <div class="job-title">{job['title']}</div>
    <div class="job-meta">📍 {job['location']} &nbsp; | &nbsp; 🕒 {job['posted']}</div>
    <div class="job-apply">
        <a href="{job['apply_link']}" target="_blank">Apply Now</a>
    </div>
</div>
""", unsafe_allow_html=True)

    else:
        st.warning("Please upload your resume first.")

elif submit4:
    if uploaded_file is not None and input_text.strip() != "":
        status = st.empty()

        status.info("📄 Reading resume...")
        pdf_content = input_pdf_setup(uploaded_file)

        status.info("🧠 Generating interview questions...")
        questions = generate_interview_questions(input_text, pdf_content)

        status.success("✅ Interview questions generated!")

        st.subheader("🎯 Interview Questions Based on Job Description")
        st.markdown(questions)

    else:
        st.warning("Please upload resume and enter Job Description.")
