from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Seed demo provider, customer, requests, bids, and bookings"

    def handle(self, *args, **kwargs):
        from auth_app.models import User
        from provider_app.models import ServiceProvider
        from service_app.models import (
            ServiceRequest, Booking, ServiceRequestBid,
            Service, SubService, Category
        )

        # --- 1. Create category ---
        plumbing_category, _ = Category.objects.get_or_create(
            name="Plumbing",
            defaults={"description": "All plumbing related services"}
        )

        # --- 2. Create provider user ---
        provider_user, _ = User.objects.get_or_create(
            email="provider@example.com",
            defaults={
                "password": "strongpassword123",  # NOTE: won't hash unless using create_user
                "phone_number": "08012345678",
                "state": "Lagos",
                "is_service_provider": True,
                "is_verified": True,
                "referral_code": "REF12345",
            }
        )
        if not provider_user.has_usable_password():
            provider_user.set_password("strongpassword123")
            provider_user.save()

        # --- 3. Create service provider profile ---
        provider, _ = ServiceProvider.objects.get_or_create(
            user=provider_user,
            defaults={
                "company_name": "QuickFix Services Ltd",
                "company_address": "123 Allen Avenue, Ikeja, Lagos",
                "company_description": "We provide plumbing, electrical, and general home maintenance services.",
                "company_phone_no": "08087654321",
                "company_email": "contact@quickfix.com",
                "business_category": plumbing_category,
                "is_approved": True,
            }
        )

        # --- 4. Create services & subservices ---
        plumbing_service, _ = Service.objects.get_or_create(
            provider=provider,
            name="Plumbing",
            defaults={
                "description": "All plumbing-related services",
                "min_price": 5000.00,
                "max_price": 8000.00,
                "category": plumbing_category
            }
        )

        sub1, _ = SubService.objects.get_or_create(
            service=plumbing_service,
            name="Pipe Installation",
            defaults={
                "description": "Install new pipes and fittings",
                "price": 7000.00
            }
        )

        sub2, _ = SubService.objects.get_or_create(
            service=plumbing_service,
            name="Leak Repair",
            defaults={
                "description": "Fix leaking pipes and taps",
                "price": 3000.00
            }
        )

        # --- 5. Create a customer user ---
        customer_user, _ = User.objects.get_or_create(
            email="customer@example.com",
            defaults={
                "password": "customerpassword123",
                "phone_number": "08123456789",
                "state": "Lagos",
                "is_service_provider": False,
                "is_verified": True,
            }
        )
        if not customer_user.has_usable_password():
            customer_user.set_password("customerpassword123")
            customer_user.save()

        # --- 6. Customer creates service requests ---
        req1, _ = ServiceRequest.objects.get_or_create(
            user=customer_user,
            title="Need new pipe installation",
            defaults={
                "description": "Require installation of water pipes in kitchen",
                "price": sub1.price,
                "category": plumbing_category,
                "latitude": 6.5244,
                "longitude": 3.3792,
                "address": "Customer House, Lagos",
            }
        )

        req2, _ = ServiceRequest.objects.get_or_create(
            user=customer_user,
            title="Fix bathroom leak",
            defaults={
                "description": "Bathroom tap leaking, needs repair",
                "price": sub2.price,
                "category": plumbing_category,
                "latitude": 6.5244,
                "longitude": 3.3792,
                "address": "Customer House, Lagos",
            }
        )

        # --- 7. Add bids for request 1 ---
        bid1, _ = ServiceRequestBid.objects.get_or_create(
            service_request=req1,
            provider=provider,
            amount=6800.00,
            latitude=6.523,
            longitude=3.375
        )
        bid1.is_accepted = True
        bid1.save()

        bid2, _ = ServiceRequestBid.objects.get_or_create(
            service_request=req1,
            provider=provider,
            amount=7200.00,
            latitude=6.526,
            longitude=3.380
        )

        booking1, _ = Booking.objects.get_or_create(
            bid=bid1,  # ✅ Link booking to accepted bid
            defaults={
                "user": bid1.service_request.user,
                "provider": bid1.provider,
                "amount": bid1.amount,
                "status": "Confirmed"
            }
        )

        # --- 8. Add bids for request 2 ---
        bid3, _ = ServiceRequestBid.objects.get_or_create(
            service_request=req2,
            provider=provider,
            amount=2800.00,
            latitude=6.524,
            longitude=3.379
        )

        bid4, _ = ServiceRequestBid.objects.get_or_create(
            service_request=req2,
            provider=provider,
            amount=3100.00,
            latitude=6.528,
            longitude=3.381
        )
        bid4.is_accepted = True
        bid4.save()

        booking2, _ = Booking.objects.get_or_create(
            bid=bid4,  # ✅ Link booking to accepted bid
            defaults={
                "user": bid4.service_request.user,
                "provider": bid4.provider,
                "amount": bid4.amount,
                "status": "Pending"
            }
        )

        # --- Final Output ---
        print("✅ Provider:", provider.company_name)
        print("✅ Customer:", customer_user.email)
        print("✅ Requests:", [req1.title, req2.title])
        print("✅ Bids for req1:", [(b.id, b.amount, b.is_accepted) for b in [bid1, bid2]])
        print("✅ Bids for req2:", [(b.id, b.amount, b.is_accepted) for b in [bid3, bid4]])
        print("✅ Bookings created:", [(booking1.id, booking1.amount, booking1.status),
                                       (booking2.id, booking2.amount, booking2.status)])

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully!"))
