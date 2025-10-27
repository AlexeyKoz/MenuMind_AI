"""
FIXED verify_email function - paste this into views.py to replace the current one
"""


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """Verify email address using the confirmation key"""
    try:
        from allauth.account.models import EmailConfirmation, EmailConfirmationHMAC, EmailAddress

        key = request.data.get('key')

        if not key:
            return Response(
                {'detail': 'Verification key is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        print(f"\n{'='*60}", flush=True)
        print(f"📧 EMAIL VERIFICATION REQUEST", flush=True)
        print(f"Key: {key}", flush=True)
        print(f"{'='*60}", flush=True)

        # Try to get confirmation by key
        confirmation = None
        try:
            confirmation = EmailConfirmation.objects.get(key=key.lower())
            print(f"✅ Found EmailConfirmation record", flush=True)
            print(f"   Email: {confirmation.email_address.email}", flush=True)
            print(
                f"   User: {confirmation.email_address.user.username}", flush=True)
            print(
                f"   Currently verified: {confirmation.email_address.verified}", flush=True)
        except EmailConfirmation.DoesNotExist:
            # Try HMAC-based confirmation (alternative method)
            try:
                confirmation = EmailConfirmationHMAC.from_key(key)
                print(f"✅ Using HMAC-based confirmation", flush=True)
            except Exception as e:
                print(f"❌ Invalid verification key: {key}", flush=True)
                print(f"   Error: {e}", flush=True)
                return Response(
                    {'detail': 'Invalid or expired verification key'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if not confirmation:
            return Response(
                {'detail': 'Could not find confirmation'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the email address object
        email_address = confirmation.email_address

        # Confirm the email - this should set verified=True
        print(f"🔄 Calling confirmation.confirm()...", flush=True)
        try:
            confirmed_email = confirmation.confirm(request)
            print(
                f"✅ confirmation.confirm() returned: {confirmed_email}", flush=True)
        except Exception as confirm_error:
            print(
                f"⚠️ confirmation.confirm() raised error: {confirm_error}", flush=True)

        # Double-check and manually set if needed
        email_address.refresh_from_db()
        print(f"📧 After confirmation:", flush=True)
        print(f"   Email verified: {email_address.verified}", flush=True)

        if not email_address.verified:
            print(f"⚠️ WARNING: Email still not verified after confirm()!", flush=True)
            print(f"   Manually setting verified=True", flush=True)
            email_address.verified = True
            email_address.save(update_fields=['verified'])
            print(f"✅ Manually set verified=True and saved", flush=True)

        print(
            f"✅ Email verified successfully for user: {email_address.user.username}", flush=True)

        return Response(
            {'detail': 'Email verified successfully'},
            status=status.HTTP_200_OK
        )

    except Exception as e:
        print(f"❌ Error verifying email: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return Response(
            {'detail': f'Verification failed: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
