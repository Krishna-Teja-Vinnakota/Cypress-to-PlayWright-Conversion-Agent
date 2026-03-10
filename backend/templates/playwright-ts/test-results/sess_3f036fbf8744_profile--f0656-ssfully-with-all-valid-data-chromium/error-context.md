# Page snapshot

```yaml
- generic [ref=e5]:
  - heading "Update Your Profile" [level=2] [ref=e6]
  - paragraph [ref=e7]: Keep your information up to date
  - generic [ref=e8]:
    - generic [ref=e9]:
      - generic [ref=e10]: Full Name *
      - textbox "Full Name *" [ref=e11]:
        - /placeholder: Enter your full name (3-50 characters)
        - text: John Doe
    - generic [ref=e12]:
      - generic [ref=e13]: Email Address *
      - textbox "Email Address *" [ref=e14]:
        - /placeholder: your.email@example.com
        - text: john.doe@example.com
    - generic [ref=e15]:
      - generic [ref=e16]: Phone Number *
      - textbox "Phone Number *" [ref=e17]:
        - /placeholder: 10 digits (e.g., 1234567890)
        - text: "1234567890"
    - generic [ref=e18]:
      - generic [ref=e19]: Age *
      - spinbutton "Age *" [ref=e20]: "30"
    - generic [ref=e21]:
      - generic [ref=e22]: Bio (Optional)
      - textbox "Bio (Optional)" [ref=e23]:
        - /placeholder: Tell us about yourself (max 200 characters)
        - text: Software Engineer
      - generic [ref=e24]: 17/200 characters
    - button "Save Profile" [ref=e25] [cursor=pointer]
  - generic [ref=e26]: ✓ Profile updated successfully
```