# RCIP (Recipe Interchange Protocol) License

**Version 1.0 - October 28, 2025**

**Copyright © 2025 Bishul.me - Alexey Kozlov**  
**Created by: Alexey Kozlov**  
**Project: Bishul.me**

---

## Purpose

The Recipe Interchange Protocol (RCIP) is an open, standardized JSON-based format for representing recipes in a machine-readable and human-readable way. This license governs the use of the RCIP specification and implementations.

## License Grant

Permission is hereby granted, free of charge, to any person or organization obtaining a copy of the RCIP specification, to use, implement, modify, and distribute RCIP implementations, subject to the following conditions:

### 1. Commercial Use Permitted

✅ You MAY use RCIP in commercial products and services without paying royalties or fees.

✅ You MAY charge for applications that use RCIP format.

✅ You MAY integrate RCIP into proprietary software.

### 2. Attribution Required

When implementing RCIP, you MUST provide attribution:

**Minimum Attribution:**
```
"This application supports RCIP (Recipe Interchange Protocol) 
by Bishul.me - https://rcip.bishul.me"
```

**Placement:**
- In application "About" section, OR
- In documentation, OR
- In API documentation, OR
- In application footer (for web apps)

**NOT required:**
- In every recipe or data file
- In user-facing features
- In marketing materials (but appreciated!)

### 3. Trademark Usage

**"RCIP" and "Recipe Interchange Protocol" are trademarks of Bishul.me.**

✅ You MAY say: "Supports RCIP format"  
✅ You MAY say: "Compatible with RCIP"  
✅ You MAY say: "Uses Recipe Interchange Protocol"

❌ You MAY NOT: Use "RCIP" or similar in your product name without permission  
❌ You MAY NOT: Imply endorsement by Bishul.me  
❌ You MAY NOT: Claim ownership of RCIP specification

### 4. Modification and Extensions

✅ You MAY extend RCIP with additional fields for your use case.

✅ You MAY create tools to convert to/from RCIP.

✅ You MAY propose improvements to the specification.

**Requirements for Extensions:**
- Use namespaced field names (e.g., `myapp_custom_field`)
- Don't break compatibility with standard RCIP fields
- Document your extensions publicly (if possible)

❌ You MAY NOT create incompatible versions and call them "RCIP".

### 5. Patent Grant

Bishul.me grants you a perpetual, worldwide, royalty-free patent license to:
- Make, use, sell, and distribute RCIP implementations
- Practice any methods or processes in the RCIP specification

**This patent grant terminates if you sue Bishul.me or any RCIP user for patent infringement related to RCIP.**

### 6. No Warranty

THE RCIP SPECIFICATION IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.

IN NO EVENT SHALL BISHUL.ME OR ALEXEY KOZLOV BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE RCIP SPECIFICATION OR THE USE OR OTHER DEALINGS IN THE SPECIFICATION.

### 7. Distribution of Specification

✅ You MAY distribute copies of the RCIP specification.

✅ You MAY translate the specification into other languages.

✅ You MAY create derivative documentation or guides.

**Requirements:**
- Include copyright notice and this license
- Don't alter the specification text itself (link to original for updates)
- Clearly mark modifications or additions

## Why RCIP Is Open

We believe recipe data should be portable and interoperable. By making RCIP open and free to use:

- 🌍 **Users benefit:** Your recipe data isn't locked into one app
- 🔧 **Developers benefit:** Build on a standard format instead of custom schemas
- 🤝 **Industry benefits:** Shared format enables innovation and collaboration
- 📈 **Bishul.me benefits:** More apps using RCIP means bigger ecosystem

## RCIP Governance

### Specification Maintenance

The RCIP specification is maintained by:
- **Primary Author:** Alexey Kozlov (Bishul.me)
- **Repository:** https://github.com/AlexeyKoz/rcip
- **Documentation:** https://docs.bishul.me/rcip

### Proposing Changes

To propose changes or improvements:
1. Open GitHub issue at https://github.com/AlexeyKoz/rcip/issues
2. Discuss with community
3. Submit pull request with proposed changes
4. Maintainers review and approve

**Criteria for acceptance:**
- Maintains backward compatibility
- Solves real problems
- Doesn't overcomplicate the specification
- Has community support

### Versioning

RCIP uses semantic versioning:
- **Major version** (1.x.x): Breaking changes
- **Minor version** (x.1.x): New features, backward compatible
- **Patch version** (x.x.1): Bug fixes, clarifications

**Current version:** 1.0.0

## Differences from Apache 2.0

This license is inspired by Apache License 2.0 but simplified:
- ✅ Attribution required (same as Apache)
- ✅ Patent grant included (same as Apache)
- ✅ Commercial use allowed (same as Apache)
- ✅ Trademark protection (same as Apache)
- ➖ Simpler language (easier to understand)
- ➖ Fewer formal requirements (more permissive)

**If there's any conflict, the Apache 2.0 principles apply.**

## Use Cases

**RCIP is perfect for:**

**Recipe Apps:**
- Import/export recipes between apps
- Share recipes with users
- Build recipe databases

**AI and Machine Learning:**
- Train AI on structured recipe data
- Generate recipes in standardized format
- Analyze recipes programmatically

**Smart Kitchen Devices:**
- Send recipes to smart ovens
- Cooking robots that follow RCIP instructions
- Voice assistants that read recipes

**Recipe Aggregators:**
- Combine recipes from multiple sources
- Standardize format across platforms
- Build recipe search engines

**Research and Analysis:**
- Nutritional research
- Culinary trend analysis
- Recipe recommendation systems

## Example Attribution

### For Web Apps

**Footer:**
```html
<footer>
  <p>Recipe format powered by 
     <a href="https://rcip.bishul.me">RCIP</a> 
     by Bishul.me
  </p>
</footer>
```

**About Page:**
```
This application uses RCIP (Recipe Interchange Protocol),
an open standard by Bishul.me for representing recipes
in a machine-readable format.

Learn more: https://rcip.bishul.me
```

### For Mobile Apps

**Settings > About:**
```
Recipe Format: RCIP (Recipe Interchange Protocol)
Developed by: Bishul.me
License: Open use with attribution
Learn more: https://rcip.bishul.me
```

### For APIs

**API Documentation:**
```markdown
## Recipe Format

This API uses RCIP (Recipe Interchange Protocol) by Bishul.me
for all recipe data.

Specification: https://rcip.bishul.me/spec
Documentation: https://docs.bishul.me/rcip
```

### For Research Papers

**Citation:**
```
Kozlov, A. (2025). RCIP: Recipe Interchange Protocol. 
Bishul.me. Retrieved from https://rcip.bishul.me
```

## FAQ

### Q: Do I need to pay to use RCIP?
**A:** No, RCIP is completely free for any use, including commercial.

### Q: Can I use RCIP in a competing recipe app?
**A:** Yes, absolutely! RCIP is open for all to use.

### Q: Do I need to open-source my app if I use RCIP?
**A:** No, RCIP can be used in proprietary software.

### Q: What if I forget attribution?
**A:** Please add it! We rely on attribution to spread awareness of RCIP.

### Q: Can I add custom fields to RCIP?
**A:** Yes, but use namespaced fields (e.g., `myapp_custom_field`).

### Q: What if RCIP doesn't support my use case?
**A:** Propose an extension or add namespaced custom fields.

### Q: Can I modify RCIP for my needs?
**A:** You can extend it, but incompatible versions can't be called "RCIP".

### Q: Is RCIP an open standard?
**A:** Yes, free to use and implement with attribution.

### Q: Who controls RCIP evolution?
**A:** Alexey Kozlov / Bishul.me maintains specification with community input.

### Q: Can robots use RCIP for cooking?
**A:** Yes! RCIP is designed for human and machine readability, including robots and smart appliances.

## Contact and Governance

### Official Specification

**Latest RCIP specification:**
- Website: https://rcip.bishul.me
- GitHub: https://github.com/AlexeyKoz/rcip
- Documentation: https://docs.bishul.me/rcip

### Questions and Support

**For RCIP-related questions:**
- Email: rcip@bishul.me
- GitHub Issues: https://github.com/AlexeyKoz/rcip/issues
- Community Forum: https://community.bishul.me/rcip

### Licensing Questions

**For licensing clarifications:**
- Email: legal@bishul.me
- Subject: "RCIP License Question"

## Version History

### Version 1.0 (October 28, 2025)
- Initial release
- Based on Apache 2.0 principles
- Patent grant included
- Attribution requirement added
- Commercial use explicitly permitted
- Created by Alexey Kozlov for Bishul.me

---

## Summary (Not Legally Binding)

**In simple terms:**

✅ **Free to use** - No cost, no royalties  
✅ **Commercial friendly** - Use in paid apps  
✅ **Patent safe** - Patent grant included  
✅ **Just attribute** - Credit Bishul.me / Alexey Kozlov  
✅ **Extend freely** - Add custom fields  
✅ **Open community** - Contribute improvements  

**Example attribution:**
```
"This app supports RCIP (Recipe Interchange Protocol) 
by Bishul.me - https://rcip.bishul.me"
```

**That's it! Now go build amazing recipe apps! 🚀**

---

© 2025 Bishul.me - Alexey Kozlov. All rights reserved.

"RCIP" and "Recipe Interchange Protocol" are trademarks of Bishul.me.

This license applies to the RCIP specification. For Bishul.me platform terms, see our Terms of Service.
