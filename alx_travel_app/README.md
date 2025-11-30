# ALX Travel App - Chapa Payment Integration

This project integrates Chapa Payment Gateway into the Django travel booking application.

## Features

- Secure payment initiation with Chapa API
- Payment status verification
- Transaction tracking and management
- Automated email notifications
- Error handling and logging

## Setup Instructions

1. Clone the repository and install dependencies:
```bash
pip install -r requirements.txt

## Models

### Listing
- Represents properties available for booking
- Fields: title, description, address, city, country, price_per_night, max_guests, bedrooms, bathrooms, property_type, amenities, is_available, host

### Booking
- Represents guest bookings
- Fields: listing, guest, check_in, check_out, total_price, guests_count, status, special_requests

### Review
- Represents guest reviews for listings
- Fields: listing, guest, rating, comment

## Serializers

### ListingSerializer
- Serializes Listing model with nested host and reviews data

### BookingSerializer
- Serializes Booking model with nested listing and guest data
- Includes validation for booking dates and guest count

## Seeding the Database

To populate the database with sample data:

```bash
python manage.py seed