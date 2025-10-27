# RCIP (Recipe Interchange Protocol) License

**Version 1.0 - October 26, 2025**

## License for the Recipe Interchange Protocol Specification

Copyright © 2025 MenuMindAI. All rights reserved.

## 1. Purpose

The Recipe Interchange Protocol (RCIP) is designed to be a universal, open format for storing and exchanging recipe data. This license permits free use, implementation, and distribution of the RCIP specification to encourage widespread adoption.

## 2. Definitions

- **"RCIP Specification"** refers to the technical documentation defining the Recipe Interchange Protocol format, including data structures, fields, and standards.
- **"Implementation"** means any software, application, or system that reads, writes, or processes RCIP format files.
- **"You"** means any individual or organization using or implementing RCIP.

## 3. Grant of Rights

### 3.1 Permission Granted

Subject to the terms of this license, you are hereby granted a perpetual, worldwide, non-exclusive, no-charge, royalty-free license to:

✅ **Use** the RCIP specification for any purpose  
✅ **Implement** RCIP in your software (commercial or non-commercial)  
✅ **Distribute** RCIP-formatted files  
✅ **Create** parsers, validators, and converters for RCIP  
✅ **Modify** RCIP files and create derivative formats  
✅ **Integrate** RCIP into existing recipe management systems  
✅ **Publish** tools and libraries that work with RCIP  

### 3.2 Commercial Use

Commercial use is explicitly permitted:
- Recipe apps and websites
- Restaurant management systems
- Smart kitchen appliances
- AI cooking assistants
- Food delivery platforms
- Recipe publishing platforms

**No royalties or licensing fees required.**

## 4. Requirements

### 4.1 Attribution

**REQUIRED:** If you implement or use RCIP, you must:

1. **Credit MenuMindAI** in your documentation:
   ```
   This application supports the Recipe Interchange Protocol (RCIP),
   developed by MenuMindAI. Learn more at https://rcip.menumindai.com
   ```

2. **Include RCIP logo** (optional but encouraged) with link to:
   - https://rcip.menumindai.com

3. **In technical documentation:**
   - Mention: "Compatible with RCIP format by MenuMindAI"
   - Link to official specification

**Acceptable Attribution Examples:**

✅ "Powered by RCIP format"  
✅ "RCIP-compatible"  
✅ "Supports Recipe Interchange Protocol (RCIP) by MenuMindAI"  
✅ "Export/Import: RCIP format"  

### 4.2 Specification Modifications

**If you modify the RCIP specification itself:**

❌ **Cannot use "RCIP" name** for incompatible versions  
✅ **Must use different name** (e.g., "ExtendedRCIP", "RCIP-Plus")  
✅ **Can propose changes** to official RCIP via GitHub  
✅ **Can extend with custom fields** (mark as extensions)  

**Backward Compatibility:**
- Extensions should not break RCIP parsers
- Use namespaced custom fields
- Document all extensions

### 4.3 No Trademark Confusion

**You may NOT:**
- Claim official endorsement by MenuMindAI without permission
- Use "MenuMindAI" branding beyond attribution
- Imply your product is made by MenuMindAI
- Register "RCIP" as your trademark

**You may:**
- Say "RCIP-compatible" or "Supports RCIP"
- Use RCIP logo with attribution
- Describe RCIP integration accurately

## 5. Patent Grant

### 5.1 Patent License

MenuMindAI grants you a perpetual, worldwide, non-exclusive, no-charge, royalty-free patent license to:
- Make, use, sell, and distribute RCIP implementations
- Use any patentable aspects of the RCIP specification

### 5.2 Patent Defense

**This patent license terminates if:**
- You initiate patent litigation against MenuMindAI or RCIP
- You claim RCIP infringes your patents

## 6. Disclaimers and Limitation of Liability

### 6.1 No Warranty

THE RCIP SPECIFICATION IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO:
- Merchantability
- Fitness for a particular purpose
- Non-infringement
- Accuracy or completeness
- Freedom from errors

### 6.2 Limitation of Liability

IN NO EVENT SHALL MENUMINDAI BE LIABLE FOR:
- Any damages arising from use of RCIP
- Data loss or corruption
- Implementation errors
- Third-party claims
- Consequential or incidental damages

**USE AT YOUR OWN RISK.**

### 6.3 Recipe Safety Disclaimer

RCIP is a data format only. MenuMindAI is NOT responsible for:
- Recipe safety or accuracy
- Allergen information accuracy
- Nutritional data correctness
- Food safety violations
- Health issues from recipes stored in RCIP format

**Recipe creators and apps bear responsibility for content.**

## 7. Contribution Terms

### 7.1 Contributing to RCIP

If you propose changes or extensions to official RCIP:
- Contributions are voluntary
- You grant MenuMindAI right to incorporate changes
- Contributors will be credited
- Contributions become part of RCIP under this license

### 7.2 Community Governance

**Official RCIP development:**
- GitHub repository: https://github.com/menumindai/rcip
- RFC process for major changes
- Community feedback encouraged
- Backward compatibility priority

### 7.3 RCIP Evolution

**Version updates:**
- Semantic versioning (e.g., RCIP 1.0, 2.0)
- Backward compatibility maintained when possible
- Breaking changes: major version bump
- Extensions: minor version bump

## 8. Implementation Guidelines

### 8.1 Validator and Tools

**Official tools available:**
- RCIP Validator (Python, JavaScript)
- JSON Schema definition
- Example files
- Conversion utilities
- Documentation and tutorials

**All tools are open source** (MIT License).

### 8.2 Certification (Optional)

**RCIP Certified** program (coming soon):
- Test your implementation
- Display certification badge
- Listed in official directory
- Free for all implementations

### 8.3 Best Practices

**Recommended:**
- Validate RCIP files before processing
- Handle missing optional fields gracefully
- Support RCIP extensions
- Preserve unknown fields when editing
- Follow semantic conventions

## 9. Comparison with Other Licenses

**RCIP License is similar to:**
- **Apache 2.0** (permissive, patent grant)
- **MIT License** (simple and permissive)

**Key differences:**
- Attribution required (unlike MIT)
- Specific to recipe data format
- Trademark protection for "RCIP" name

## 10. Frequently Asked Questions

### Q: Can I use RCIP in my commercial app?
**A:** Yes! Free for commercial use with attribution.

### Q: Do I need to open-source my RCIP implementation?
**A:** No. Your code can be proprietary. Only attribution required.

### Q: Can I charge for an app that uses RCIP?
**A:** Yes. RCIP is royalty-free for commercial use.

### Q: Can I add custom fields to RCIP?
**A:** Yes, but use namespaced fields (e.g., `myapp_custom_field`).

### Q: What if RCIP doesn't support my use case?
**A:** Propose an extension or add namespaced custom fields.

### Q: Can I modify RCIP for my needs?
**A:** You can extend it, but incompatible versions can't be called "RCIP".

### Q: Is RCIP an open standard?
**A:** Yes, free to use and implement with attribution.

### Q: Who controls RCIP evolution?
**A:** MenuMindAI maintains specification with community input.

### Q: Can robots use RCIP for cooking?
**A:** Yes! RCIP is designed for human and machine readability, including robots and smart appliances.

## 11. Contact and Governance

### 11.1 Official Specification

**Latest RCIP specification:**
- Website: https://rcip.menumindai.com
- GitHub: https://github.com/menumindai/rcip
- Documentation: https://docs.menumindai.com/rcip

### 11.2 Questions and Support

**For RCIP-related questions:**
- Email: rcip@menumindai.com
- GitHub Issues: https://github.com/menumindai/rcip/issues
- Community Forum: https://community.menumindai.com/rcip

### 11.3 Licensing Questions

**For licensing clarifications:**
- Email: legal@menumindai.com
- Subject: "RCIP License Question"

## 12. Version History

### Version 1.0 (October 26, 2025)
- Initial release
- Based on Apache 2.0 style
- Patent grant included
- Attribution requirement added
- Commercial use explicitly permitted

---

## Summary (Not Legally Binding)

**In simple terms:**

✅ **Free to use** - No cost, no royalties  
✅ **Commercial friendly** - Use in paid apps  
✅ **Patent safe** - Patent grant included  
✅ **Just attribute** - Credit MenuMindAI  
✅ **Extend freely** - Add custom fields  
✅ **Open community** - Contribute improvements  

**Example attribution:**
```
"This app supports RCIP (Recipe Interchange Protocol) 
by MenuMindAI - https://rcip.menumindai.com"
```

**That's it! Now go build amazing recipe apps! 🚀**

---

© 2025 MenuMindAI. All rights reserved.

"RCIP" and "Recipe Interchange Protocol" are trademarks of MenuMindAI.

This license applies to the RCIP specification. For MenuMindAI platform terms, see our Terms of Service.