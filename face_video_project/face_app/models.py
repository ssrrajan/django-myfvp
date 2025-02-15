from django.db import models
from django.core.validators import RegexValidator, EmailValidator
from django.core.exceptions import ValidationError

class RegTb(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False)
    mobile = models.CharField(
        max_length=10,
        unique=True,
        validators=[RegexValidator(regex=r'^\d{10}$', message="Mobile number must be exactly 10 digits.")],
        blank=False,
        null=False
    )
    email = models.EmailField(unique=True, validators=[EmailValidator()], blank=False, null=False)
    address = models.TextField(blank=False, null=False)
    username = models.CharField(max_length=50, unique=True, blank=False, null=False)
    password = models.CharField(max_length=50, blank=False, null=False)

    def __str__(self):
        return self.username

class ComplaintTb(models.Model):
    STATUS_CHOICES = [
        ('New Complaint', 'New Complaint'),
        ('Investigation in Progress', 'Investigation in Progress'),
        ('Face Matched', 'Face Matched'),
        ('Match Failed', 'Match Failed'),
        ('Closed', 'Closed'),
    ]
    complaint_no = models.CharField(max_length=20, unique=True)
    username = models.ForeignKey('RegTb', on_delete=models.CASCADE)
    mobile = models.CharField(max_length=15)
    name = models.CharField(max_length=100)
    umobile = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    filename = models.ImageField(upload_to='uploads/', null=True, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='New Complaint')

    def __str__(self):
        return f"{self.complaint_no} - {self.name}"

class InvestigationTb(models.Model):
    STATUS_CHOICES = [
        ('Video Loaded', 'Video Loaded'),
        ('Face Matched', 'Face Matched'),
        ('Match Failed', 'Match Failed'),
        ('Closed', 'Closed'),
    ]
    complaint = models.ForeignKey('face_app.ComplaintTb', on_delete=models.CASCADE, related_name='investigation')
    video_file = models.FileField(upload_to='investigations/', null=True, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Video Loaded')
    timestamp = models.DateTimeField(auto_now_add=True)
    matched_frame = models.ImageField(upload_to='matched_screenshots/', null=True, blank=True)
    matched_time = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Investigation for {self.complaint.complaint_no}"