#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Monitor Real-Time Registration"""
import os
import sys
import codecs

if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menumine_ai.settings')
import django
django.setup()

from apps.users.models import User, UserPreferences

print("="*70)
print("Watching for new registrations...")
print("="*70)
print("\nShowing LATEST 5 users and their language settings:\n")

users = User.objects.all().order_by('-date_joined')[:5]

for user in users:
    prefs = UserPreferences.objects.filter(user=user).first()
    
    print(f"User: {user.username}")
    print(f"  Email: {user.email}")
    print(f"  Joined: {user.date_joined}")
    print(f"  Language: {prefs.language if prefs else 'N/A'}")
    print()

print("="*70)
print("\n🔍 NOW REGISTER A NEW USER FROM FRONTEND")
print("Then run this script again to see the language!")
print("="*70)

