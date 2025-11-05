from django.contrib.auth import get_user_model

User = get_user_model()

# Check if admin exists
if User.objects.filter(username='admin').exists():
    print("Admin user already exists")
    user = User.objects.get(username='admin')
    # Update password
    user.set_password('BishulAdmin2025!')
    user.save()
    print("Password updated for existing admin user")
else:
    # Create new superuser
    user = User.objects.create_superuser(
        username='admin',
        email='admin@bishul.me',
        password='BishulAdmin2025!'
    )
    print("New superuser created successfully")

print(f"\n✅ Admin credentials:")
print(f"   Username: admin")
print(f"   Password: BishulAdmin2025!")
print(f"   Email: admin@bishul.me")
print(f"\n🔗 Access admin at: http://localhost:8000/admin/")

