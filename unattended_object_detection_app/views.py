from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User, Group
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
import numpy as np             #numpy,cv2 imported - required libraries
import cv2
from twilio.rest import Client
from django.http import HttpResponse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import cv2
import win32gui
import win32con
import os
from django.contrib.auth import get_user_model
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib.auth.forms import PasswordResetForm
from .models import CustomUser



# Create your views here.

def login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)  
        phone_number = request.CustomUser.phone_number
        
        if user:
            login(request, user)
            return render(request,'home.html',{'phone_number':phone_number})
        else:
            messages.error(request, "Incorrect Login credentials")
            return redirect('login')
            #return render(request, 'login.html', {})
    else:
        return render(request, 'login.html', {})

@login_required
def home(request):

    if request.method == "POST":
        e = request.POST["email"]
        p = request.POST["phone"]
        v = request.POST["video"]
        path = 'media/videos/' + v
        cap = cv2.VideoCapture(path)      #reading input video frame by frame

        _, BG= cap.read()                         #saving first frame as background frame
        #cv2.imshow('Main Background', BG)         #Output as main background
        BG=cv2.cvtColor(BG,cv2.COLOR_BGR2GRAY)    #changing backgroung image to gray scale
        cv2.equalizeHist(BG)                      #increasing contrast of the image
        BG=cv2.GaussianBlur(BG,(7,7),0)           #applying gaussian filtering
        GUI = BG
        denoise_median = cv2.medianBlur(GUI, 5)   #applying median filtering
        d,count,d1,r1,mail_count,msg_count = 0,{},[],[],0,0


        account_sid = 'Your_account_sid'
        auth_token = 'Your_auth_token'

        client = Client(account_sid, auth_token)


        smtp_server = 'smtp.gmail.com'
        smtp_port = 587
        smtp_username = 'Your_mail_id'
        smtp_password = 'Your_password'
        recipient = e

        # Create a multipart message object
        msg = MIMEMultipart()

        # Add the text message
        text = MIMEText("An Unattended Object Detected!! Stay Alert")
        msg.attach(text)


        while (cap.isOpened()):
            ret, frame = cap.read()

            if ret == 0:
                break
            gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)   #for each frame - image to gray scale
            cv2.equalizeHist(gray)                          #for each frame - histogram equalization
            gray = cv2.GaussianBlur(gray,(7,7),0)           #for each frame - gaussian filtering
            median = cv2.medianBlur(gray, 5)                #for each frame - median filtering

            absdiff_mask = cv2.absdiff(median.astype(np.uint8), denoise_median.astype(np.uint8))  #to detect exact pixels of moving object
            #cv2.imshow("Testing",absdiff_mask)

            rt,absdiff_mask = cv2.threshold(absdiff_mask.astype(np.uint8),25,255,cv2.THRESH_BINARY)  #to binarize the image, either black(0) or white(1)
            #cv2.imshow("Testing",absdiff_mask)
            morph = np.ones((8,8),np.uint8)
            morphs = cv2.morphologyEx(absdiff_mask,cv2.MORPH_CLOSE,morph,iterations=3)              #to perfom morphological operations

            canyedge = cv2.Canny(morphs,30,50)                                                      #to perform canny edge detection

            
            #print(cv2.findContours(canyedge,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE))
            
            contours,hierarchy = cv2.findContours(canyedge,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)       #to perform contour tracking
            #print(contours)


            count[d%1000] = []
            for i in contours:
                middle = cv2.moments(i)
                if not middle['m00'] == 0:          #finding centroid of object
                    xaxis = int(middle['m10']/middle['m00'])            #finding x axis of centriod
                    yaxis = int(middle['m01']/middle['m00'])            #finding y axis of centroid
                    centre = (xaxis,yaxis)                              #centroid of the object

                    count[d%1000].append(centre)                        #appending centroid value into the list

                    if d==20:
                        (x,y,w,h) = cv2.boundingRect(i)
                        denoise_median[y:y+h,x:x+w] = gray[y:y+h,x:x+w]


                    if d>200:                                           #200 frame count
                        if cv2.contourArea(i) in range(200,12500) and centre in count[(d-190)%1000] and count[(d-100)%1000] and count[(d-50)%1000]:         #checking the area of object and object exist in previous frames
                            (x,y,w,h) = cv2.boundingRect(i)             #boundaries of the object
                            d1.append(centre)
                            if d1.count(centre)>10:
                                cv2.rectangle(frame, (x,y), (x+w,y+h), (0,0,255),2)         #rectangle around the object
                                cv2.putText(frame,'unattended object',(x,y-10),cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255),2)        #text for the rectangle
                                if len(r1)==0: r1.append(centre)
                                imagename = str(d)+'.jpg'
                                cv2.imwrite(imagename, frame)
                                r = ''
                                if p[0] != '+':
                                    r = '+91'
                                r += p
                                if msg_count%7==0:
                                    message = client.messages.create(
                                            from_='Twilio_mobile_number',
                                            body ='Unattended Object detected',
                                            to =r)
                                msg_count += 1
                                

                                #if centre not in r1:
                                with open(imagename, 'rb') as f:
                                    img_data = f.read()

        # Create a SMTP connection and send the message
                                if r1.count(centre)<=1:
                                    img = MIMEImage(img_data, name='unattended.jpg')
                                    msg.attach(img)
                                    server = smtplib.SMTP(smtp_server, smtp_port)
                                    server.starttls()
                                    server.login(smtp_username, smtp_password)
                                    server.sendmail(smtp_username, recipient, msg.as_string())
                                    mail_count += 1
                                r1.append(centre)
                                

                                os.remove(imagename)

            if(cv2.waitKey(1) & 0xFF == ord('x')):              
                denoise_median[y:y+h,x:x+w] = gray[y:y+h,x:x+w]         #background updating for the wrong detected objects

           
            d += 1
            #cv2.imshow('result',canyedge)                   #output for result - cannyedge
            frame = cv2.resize(frame,(1500,720))
            cv2.imshow('original',frame)                    #output for original video

            # Find the OpenCV window by its title
            hwnd = win32gui.FindWindow(None, 'original')

            # Set the window as the foreground window
            #win32gui.BringWindowToTop(hwnd)
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                       win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)


            # Show the window if it is minimized
            # if win32gui.IsIconic(hwnd):
            #     win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

            if(cv2.waitKey(1) & 0xFF == ord('q')):          #q for quit
                break
            
        cap.release()
        cv2.destroyAllWindows()


    return render(request, 'home.html')
    #return response


@login_required
def add_user(request):
    User = get_user_model() 
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Create new user object
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                phone_number=form.cleaned_data['phone_number'],
                date_of_birth = form.cleaned_data['date_of_birth'],
                place = form.cleaned_data['place'],
                question = form.cleaned_data['question']
            )
            # user=form.save()
            # Set user permissions
            admin_group = Group.objects.get(name='Admin')
            user.groups.add(admin_group)
            user.save()
            messages.success(request, 'User added successfully.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'adduser.html', {'form': form})


# def login_user(request):
#     return render(request, 'login.html')


class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = '/password_reset/done/'

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = '/reset/done/'

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'


def password_reset(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(
                # domain_override='example.com',
                email_template_name='password_reset_email.html'
            )
            messages.success(request, 'Password reset email sent.')
    else:
        form = PasswordResetForm()
    return render(request, 'password_reset_form.html', {'form': form})
