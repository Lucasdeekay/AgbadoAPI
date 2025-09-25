from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Seed demo provider, customer, requests, bids, and bookings"

    def handle(self, *args, **kwargs):
        from auth_app.models import User
        from provider_app.models import ServiceProvider, Service, SubService
        from service_app.models import ServiceRequest, Booking, ServiceRequestBid

        # --- 1. Create provider user ---
        provider_user = User.objects.create_user(
            email="provider@example.com",
            password="strongpassword123",
            phone_number="08012345678",
            state="Lagos",
            is_service_provider=True,
            is_verified=True
        )
        provider_user.referral_code = "REF12345"
        provider_user.save()

        # --- 2. Create service provider profile ---
        provider = ServiceProvider.objects.create(
            user=provider_user,
            company_name="QuickFix Services Ltd",
            company_address="123 Allen Avenue, Ikeja, Lagos",
            company_description="We provide plumbing, electrical, and general home maintenance services.",
            company_phone_no="08087654321",
            company_email="contact@quickfix.com",
            business_category="Plumbing",
            is_approved=True
        )

        # --- 3. Create services & subservices ---
        plumbing_service = Service.objects.create(
            provider=provider,
            name="Plumbing",
            description="All plumbing-related services",
            price=5000.00,
            category="Plumbing"
        )

        sub1 = SubService.objects.create(
            service=plumbing_service,
            name="Pipe Installation",
            description="Install new pipes and fittings",
            price=7000.00
        )
        sub2 = SubService.objects.create(
            service=plumbing_service,
            name="Leak Repair",
            description="Fix leaking pipes and taps",
            price=3000.00
        )

        # --- 4. Create a customer user ---
        customer_user = User.objects.create_user(
            email="customer@example.com",
            password="customerpassword123",
            phone_number="08123456789",
            state="Lagos",
            is_service_provider=False,
            is_verified=True
        )

        # --- 5. Customer creates service requests ---
        req1 = ServiceRequest.objects.create(
            user=customer_user,
            title="Need new pipe installation",
            description="Require installation of water pipes in kitchen",
            price=sub1.price,
            category="Plumbing",
            latitude=6.5244,
            longitude=3.3792,
            address="Customer House, Lagos"
        )

        req2 = ServiceRequest.objects.create(
            user=customer_user,
            title="Fix bathroom leak",
            description="Bathroom tap leaking, needs repair",
            price=sub2.price,
            category="Plumbing",
            latitude=6.5244,
            longitude=3.3792,
            address="Customer House, Lagos"
        )

        # --- 6. Add bids for request 1 ---
        bid1 = ServiceRequestBid.objects.create(
            request=req1,
            provider=provider,
            proposed_amount=6800.00,
            latitude=6.523,
            longitude=3.375
        )

        bid2 = ServiceRequestBid.objects.create(
            request=req1,
            provider=provider,
            proposed_amount=7200.00,
            latitude=6.526,
            longitude=3.380
        )

        # Accept bid1 → create booking
        accepted_bid = bid1
        accepted_bid.is_accepted = True
        accepted_bid.save()

        booking1 = Booking.objects.create(
            request=req1,
            provider=accepted_bid.provider,
            amount=accepted_bid.proposed_amount,
            status="Confirmed"
        )

        # --- 7. Add bids for request 2 ---
        bid3 = ServiceRequestBid.objects.create(
            request=req2,
            provider=provider,
            proposed_amount=2800.00,
            latitude=6.524,
            longitude=3.379
        )

        bid4 = ServiceRequestBid.objects.create(
            request=req2,
            provider=provider,
            proposed_amount=3100.00,
            latitude=6.528,
            longitude=3.381
        )

        # Accept bid4 → create booking
        accepted_bid2 = bid4
        accepted_bid2.is_accepted = True
        accepted_bid2.save()

        booking2 = Booking.objects.create(
            request=req2,
            provider=accepted_bid2.provider,
            amount=accepted_bid2.proposed_amount,
            status="Pending"
        )

        print("✅ Provider:", provider.company_name)
        print("✅ Customer:", customer_user.email)
        print("✅ Requests:", [req1.title, req2.title])
        print("✅ Bids for req1:", [(b.id, b.proposed_amount, b.is_accepted) for b in [bid1, bid2]])
        print("✅ Bids for req2:", [(b.id, b.proposed_amount, b.is_accepted) for b in [bid3, bid4]])
        print("✅ Bookings created:", [(booking1.id, booking1.amount, booking1.status),
                                    (booking2.id, booking2.amount, booking2.status)])

        
        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully!"))
