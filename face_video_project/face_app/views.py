from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import RegTb, ComplaintTb, InvestigationTb
import os
from django.conf import settings
import uuid
from django.urls import reverse
import cv2
import numpy as np
from django.core.files.storage import default_storage
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
import insightface
from insightface.app import FaceAnalysis
from django.core.mail import send_mail



def home(request):
    return render(request, 'index.html')

def admin_login(request):
    if request.method == 'POST':
        uname = request.POST.get('uname')
        password = request.POST.get('password')
        if uname == 'admin' and password == 'admin':
            data = RegTb.objects.all()
            # messages.success(request, "You have successfully logged in!")
            return render(request, 'AdminHome.html', {'data': data})
        # else:
        #     # messages.error(request, "Username or Password Incorrect!")
    return render(request, 'AdminLogin.html')

def admin_home(request):
    return render(request, 'AdminHome.html')


def user_list(request):
    users = RegTb.objects.all()
    return render(request, 'UsersList.html', {'users': users})

def complaint_list(request):
    complaints = ComplaintTb.objects.all()
    return render(request, 'ComplaintList.html', {'complaints': complaints})

def user_login(request):
    if request.method == 'POST':
        uname = request.POST.get('uname')
        password = request.POST.get('password')
        try:
            user = RegTb.objects.get(username=uname, password=password)
            request.session['uname'] = uname
            # messages.success(request, "You have successfully logged in!")
            return render(request, 'UserHome.html', {'data': user})
        except RegTb.DoesNotExist:
            # messages.error(request, 'Username or Password is incorrect.')
            return render(request, 'UserLogin.html')
    return render(request, 'UserLogin.html')

def user_home(request):
    uname = request.session.get('uname')
    if not uname:
        return redirect('user_login')  # Redirect to login if not authenticated
    user = get_object_or_404(RegTb, username=uname)
    return render(request, 'UserHome.html', {'data': user})

def new_user(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        mobile = request.POST.get('mobile')
        email = request.POST.get('email')
        address = request.POST.get('address')
        uname = request.POST.get('uname')
        password = request.POST.get('password')

        # Backend validation
        if not name or not mobile or not email or not address or not uname or not password:
            messages.error(request, "All fields are required.")
            return render(request, 'NewUser.html')

        if not mobile.isdigit() or len(mobile) != 10:
            messages.error(request, "Mobile number must be exactly 10 digits.")
            return render(request, 'NewUser.html')

        if RegTb.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return render(request, 'NewUser.html')

        if RegTb.objects.filter(mobile=mobile).exists():
            messages.error(request, "Mobile number is already registered.")
            return render(request, 'NewUser.html')

        # Save user
        try:
            user = RegTb.objects.create(
                name=name, mobile=mobile, email=email, address=address, username=uname, password=password
            )

            # Send email notification
            subject = "Welcome to Complaint Management System"
            message = f"""
            Dear {name},

            Your account has been successfully registered.

            Here are your details:
            Username: {uname}
            Email: {email}
            Mobile: {mobile}
            Address: {address}

            You can now log in and file complaints.

            Regards,
            Complaint Management System Team
            """
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

            messages.success(request, "Registration successful! Email sent.")
            return redirect('user_login')

        except ValidationError as e:
            messages.error(request, str(e))
            return render(request, 'NewUser.html')

    return render(request, 'NewUser.html')

def new_complaint(request):
    if request.method == 'POST':
        uname = request.session.get('uname')  # Get username from session
        name = request.POST.get('name')
        umobile = request.POST.get('mobile')
        email = request.POST.get('email')  # This is the missing person's email (not needed for notification)
        address = request.POST.get('address')
        file = request.FILES['file']

        # Generate a unique complaint number
        complaint_no = f"CMP-{uuid.uuid4().hex[:8].upper()}"

        try:
            # Fetch the registered user
            user_instance = RegTb.objects.get(username=uname)

            # Save the complaint
            complaint = ComplaintTb.objects.create(
                complaint_no=complaint_no,
                username=user_instance,
                name=name,
                mobile=umobile,
                email=email,  # Keeping this field for complaint data, but not using it for email
                address=address,
                filename=file,
                status='New Complaint'
            )

            # Send email notification to the registered user's email
            subject = f"New Complaint Registered: {complaint_no}"
            message = f"""
            Dear {user_instance.name},

            Your complaint has been successfully registered.

            Complaint Details:
            Complaint Number: {complaint_no}
            Missing Person's Name: {name}
            Missing Person's Mobile: {umobile}
            Last Seen Location: {address}
            Status: New Complaint

            We will keep you updated on further investigation.

            Regards,
            Complaint Management System Team
            """

            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_instance.email])  # Sending to RegTb email

            messages.success(request, f"Complaint {complaint_no} Posted Successfully! Email Sent.")
            return redirect(reverse('u_complaint_info', kwargs={'complaint_no': complaint.complaint_no}))

        except RegTb.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('new_complaint')

    return render(request, 'NewComplaint.html')

def user_complaints(request):
    uname = request.session.get('uname')  # Use 'uname' instead of 'username'
    if uname:
        complaints = ComplaintTb.objects.filter(username__username=uname)  # Filter complaints by username
        return render(request, 'user_complaints.html', {'complaints': complaints})
    else:
        # messages.error(request, "You are not logged in!")
        return redirect('user_login')

def complaint_detail(request, complaint_no):
    complaint = get_object_or_404(ComplaintTb, complaint_no=complaint_no)
    return render(request, 'ComplaintDetail.html', {'complaint': complaint})


def u_complaint_info(request, complaint_no):
    complaint = get_object_or_404(ComplaintTb, complaint_no=complaint_no)
    return render(request, 'UComplaintInfo.html', {'complaint': complaint})


def upload_video(request, complaint_no):
    complaint = get_object_or_404(ComplaintTb, complaint_no=complaint_no)
    investigation, created = InvestigationTb.objects.get_or_create(
        complaint=complaint,
        defaults={'status': 'Video Loaded'}
    )

    allowed_video_formats = ['video/mp4', 'video/avi', 'video/mkv', 'video/webm', 'video/mov']

    if request.method == 'POST' and 'video_file' in request.FILES:
        video_file = request.FILES['video_file']

        if video_file.content_type not in allowed_video_formats:
            return render(request, 'UploadVideo.html', {'investigation': investigation})

        investigation.video_file = video_file
        investigation.status = 'Video Loaded'
        investigation.save()

        # Update complaint status to "Investigation in Progress"
        complaint.status = "Investigation in Progress"
        complaint.save()

        # Send email notification
        subject = f"Complaint {complaint.complaint_no} - Video Uploaded"
        message = f"""
        Dear {complaint.username.name},

        A new video has been uploaded for your complaint ({complaint.complaint_no}).

        Status: Investigation in Progress

        We will notify you of further updates.

        Regards,
        Complaint Management System Team
        """
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [complaint.username.email])

        return redirect('complaint_list')

    return render(request, 'UploadVideo.html', {'investigation': investigation})
	
face_app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
face_app.prepare(ctx_id=0, det_size=(640, 640))

def extract_face_embedding(image):
    """Extracts face embedding from an image using InsightFace."""
    if isinstance(image, str):  # If it's a file path
        img = cv2.imread(image)
    elif isinstance(image, np.ndarray):  # If it's a frame from a video
        img = image
    else:
        print(f"Invalid image input: {type(image)}")
        return None

    if img is None:
        print(f"Error loading image: {image}")
        return None

    faces = face_app.get(img)
    return faces[0].normed_embedding if faces else None

def cosine_similarity(embedding1, embedding2):
    """Computes cosine similarity between two face embeddings."""
    return np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))

def face_match(request, complaint_no):
    complaint = get_object_or_404(ComplaintTb, complaint_no=complaint_no)
    investigation = InvestigationTb.objects.filter(complaint=complaint).last()

    if not investigation or not investigation.video_file:
        return redirect('complaint_list')

    if request.method == 'POST':
        video_path = default_storage.path(investigation.video_file.name)
        video_capture = cv2.VideoCapture(video_path)

        if not video_capture.isOpened():
            return redirect('complaint_list')

        fps = video_capture.get(cv2.CAP_PROP_FPS)
        frame_count = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps

        complaint_image_path = complaint.filename.path if complaint.filename else None
        if not complaint_image_path or not os.path.exists(complaint_image_path):
            return redirect('complaint_list')

        complaint_embedding = extract_face_embedding(complaint_image_path)
        if complaint_embedding is None:
            return redirect('complaint_list')

        matched_frame = None
        matched_time = None
        match_found = False
        frame_index = 0

        while video_capture.isOpened():
            ret, frame = video_capture.read()
            if not ret:
                break

            face_embedding = extract_face_embedding(frame) if frame is not None else None
            if face_embedding is not None:
                similarity_score = cosine_similarity(complaint_embedding, face_embedding)

                if similarity_score > 0.6:
                    matched_frame = frame
                    matched_time = frame_index / fps
                    match_found = True
                    break  

            frame_index += 1

        video_capture.release()

        with transaction.atomic():
            if match_found:
                investigation.status = "Face Matched"
                complaint.status = "Face Matched"
                investigation.matched_time = round(matched_time, 2)

                matched_frame_filename = f"matched_screenshots/{complaint.complaint_no}_match.jpg"
                _, buffer = cv2.imencode('.jpg', matched_frame)
                file_content = ContentFile(buffer.tobytes())
                investigation.matched_frame.save(matched_frame_filename, file_content, save=True)

                # Send email for face match success
                subject = f"Complaint {complaint.complaint_no} - Face Matched"
                message = f"""
                Dear {complaint.username.name},

                A face match has been found in the uploaded video for your complaint ({complaint.complaint_no}).

                Status: Face Matched
                Matched Time: {matched_time:.2f} seconds

                You can review the matched frame in the system.

                Regards,
                Complaint Management System Team
                """
            else:
                investigation.status = "Match Failed"
                complaint.status = "Match Failed"

                # Send email for face match failure
                subject = f"Complaint {complaint.complaint_no} - Match Failed"
                message = f"""
                Dear {complaint.username.name},

                No matching face was found in the uploaded video for your complaint ({complaint.complaint_no}).

                Status: Match Failed

                You may upload a clearer image or contact the authorities for further action.

                Regards,
                Complaint Management System Team
                """

            investigation.save()
            complaint.save()

            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [complaint.username.email])

        return redirect('complaint_list')

    return render(request, 'FaceMatch.html', {'complaint': complaint, 'investigation': investigation})

def investigation_details(request, complaint_no):
    investigation = get_object_or_404(InvestigationTb, complaint__complaint_no=complaint_no, status="Face Matched")
    return render(request, 'InvestigationDetails.html', {'investigation': investigation})
	
def investigation_list(request):
    investigations = InvestigationTb.objects.select_related('complaint').all()
    return render(request, 'InvestigationList.html', {'investigations': investigations})