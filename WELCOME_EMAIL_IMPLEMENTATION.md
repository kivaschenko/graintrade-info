# Welcome Email Implementation for New Users

## Overview
This implementation adds a greeting email feature for newly registered users. When a user registers, their data is sent to the `user.events` RabbitMQ queue, and the notification service sends them welcome emails in both English and Ukrainian languages.

## Changes Made

### 1. Email Templates Created
Two new HTML email templates were created:

#### `/notifications/app/templates/welcome_email_en.html`
- **Language**: English
- **Subject**: "Welcome to GrainTrade Info! 🌾"
- **Content**:
  - Personalized greeting
  - Introduction to the platform
  - Link to "How To" guide: https://home.graintrade.info/how-to?lang=en
  - List of platform features
  - Contact information encouraging feedback to info@graintrade.info
  - Professional styling with green theme

#### `/notifications/app/templates/welcome_email_ua.html`
- **Language**: Ukrainian (Українська)
- **Subject**: "Ласкаво просимо до GrainTrade Info! 🌾"
- **Content**:
  - Personalized greeting in Ukrainian
  - Introduction to the platform
  - Link to "How To" guide: https://home.graintrade.info/how-to?lang=uk
  - List of platform features
  - Contact information encouraging feedback to info@graintrade.info
  - Professional styling with green theme

### 2. Consumer Handler Added

#### `/notifications/app/consumers.py`
Added new async function `handle_user_registration_notification()`:

**Features:**
- Processes messages from `user.events` queue
- Validates email presence
- Sends **both** English and Ukrainian welcome emails
- Uses user's full name or username as fallback
- Comprehensive error handling and logging
- Respects `ENABLE_EMAIL` configuration flag

**Expected Message Format:**
```json
{
    "username": "maximus",
    "email": "max@example.com",
    "full_name": "Max Cat",
    "phone": "",
    "disabled": "False",
    "hashed_password": "$2b$12$...",
    "id": "9"
}
```

### 3. Consumer Registration

#### `/notifications/app/main.py`
- Imported `handle_user_registration_notification` from consumers
- Registered consumer for `QueueName.USER_EVENTS` queue
- Added logging for queue consumption

## Email Content Features

Both email templates include:

1. **Welcoming Header** with grain emoji 🌾
2. **Personalized Greeting** using user's full name
3. **Call-to-Action Button** linking to the "How To" guide
4. **Feature Highlights**:
   - Post grain and agricultural product listings
   - Browse offers from verified sellers and buyers
   - Connect directly with trading partners
   - Get real-time commodity price updates
   - Manage business preferences and notifications

5. **Contact Section**:
   - Appreciation message
   - Encouragement for feedback
   - Email contact: info@graintrade.info

6. **Professional Design**:
   - Responsive layout
   - Clean typography
   - Green color scheme (#28a745) matching agricultural theme
   - Box shadows and rounded corners
   - Mobile-friendly styling

## Testing the Implementation

To test this feature:

1. Ensure the notifications service is running
2. Register a new user through the backend service
3. Check that the message is published to `user.events` queue
4. Verify that both English and Ukrainian emails are sent
5. Check logs for confirmation messages

## Configuration

The feature respects the following environment variables:
- `ENABLE_EMAIL`: Must be `True` to send emails
- Email server configuration (used by `send_email` function)

## Future Enhancements

Possible improvements:
- Add user language preference to send only one email in their preferred language
- Add unsubscribe link
- Track email opens/clicks
- A/B testing different email content
- Add more personalization based on user's selected categories or location

## Notes

- Both language versions are sent to ensure the user receives information in a language they understand
- The implementation is fully async for optimal performance
- Error handling ensures the service continues running even if email sending fails
- All actions are properly logged for monitoring and debugging
