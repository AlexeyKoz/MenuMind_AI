#!/usr/bin/env python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menumine_ai.settings')
import django
django.setup()

from allauth.account.models import EmailAddress

print("Fixing email verification...")

# Get all duplicate emails
email = 'menumindaiproject@gmail.com'
records = EmailAddress.objects.filter(email=email)

print(f"Found {records.count()} EmailAddress records for {email}")

if records.count() > 1:
    print("Removing duplicates...")
    # Keep the first one, delete the rest
    keep = records.first()
    records.exclude(id=keep.id).delete()
    print(f"Kept record ID: {keep.id}")

# Now verify the remaining one
ea = EmailAddress.objects.filter(email=email).first()
if ea:
    ea.verified = True
    ea.save()
    print(f"✅ Email {email} is now verified!")
    print(f"   Primary: {ea.primary}")
    print(f"   Verified: {ea.verified}")
    print("\nNow:")
    print("1. Logout from frontend")
    print("2. Login again")
    print("3. Banner should be gone!")
else:
    print(f"❌ No email address found")

