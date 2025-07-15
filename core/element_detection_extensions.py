#!/usr/bin/env python3
"""
Advanced Element Detection Extensions for Web Element Analyzer

This module provides additional detection methods for the WebElementAnalyzer class to identify
framework-specific elements (Angular, React), form structures, accessibility features,
and dynamic content.

These functions can be integrated into the WebElementAnalyzer class to enhance its capabilities.
"""

class AdvancedDetectionExtensions:
    """
    Methods to detect framework-specific elements and advanced web features
    These should be added to the WebElementAnalyzer class to extend its functionality
    """
    
    def _perform_advanced_detection(self):
        """Orchestrates the detection of framework-specific elements"""
        print("Performing advanced element detection...")
        if not self.page or not self.output_dir:
            print("Error: Page or output directory not initialized for advanced detection.")
            return
            
        try:
            # Detect Angular elements
            angular_elements = self._detect_angular_elements()
            with open(f"{self.output_dir}/angular_elements.json", "w", encoding="utf-8") as f:
                json.dump(angular_elements, f, indent=2)
            print(f"Angular elements saved: {len(angular_elements.get('components', []))} components, {len(angular_elements.get('bindings', []))} bindings")
            
            # Detect React elements
            react_elements = self._detect_react_elements()
            with open(f"{self.output_dir}/react_elements.json", "w", encoding="utf-8") as f:
                json.dump(react_elements, f, indent=2)
            print(f"React elements saved: {len(react_elements.get('components', []))} components")
            
            # Detect form elements
            form_elements = self._detect_form_elements()
            with open(f"{self.output_dir}/form_elements.json", "w", encoding="utf-8") as f:
                json.dump(form_elements, f, indent=2)
            print(f"Form elements saved: {len(form_elements.get('forms', []))} forms, {len(form_elements.get('formGroups', []))} form groups")
            
            # Detect accessibility features
            accessibility_elements = self._detect_accessible_elements()
            with open(f"{self.output_dir}/accessibility_elements.json", "w", encoding="utf-8") as f:
                json.dump(accessibility_elements, f, indent=2)
            print(f"Accessibility elements saved: {len(accessibility_elements.get('ariaElements', []))} ARIA elements, {len(accessibility_elements.get('accessibilityIssues', []))} issues")
            
            # Detect dynamic content
            dynamic_content = self._detect_dynamic_content()
            with open(f"{self.output_dir}/dynamic_content.json", "w", encoding="utf-8") as f:
                json.dump(dynamic_content, f, indent=2)
            print(f"Dynamic content saved: {len(dynamic_content.get('dynamicAreas', []))} areas, {len(dynamic_content.get('ajaxElements', []))} AJAX elements")
            
            # Store the framework data for later use
            self.framework_data = {
                "angular": angular_elements,
                "react": react_elements,
                "forms": form_elements,
                "accessibility": accessibility_elements,
                "dynamic": dynamic_content
            }
            
            # Generate advanced descriptors
            self._generate_advanced_descriptors()
            
            print("Advanced element detection completed successfully")
            
        except Exception as e:
            print(f"Error during advanced element detection: {e}")
            import traceback
            traceback.print_exc()
    
    def _detect_angular_elements(self):
        """
        Detect and extract Angular-specific elements and bindings
        
        Returns:
            Dictionary of Angular elements and bindings
        """
        print("Detecting Angular elements...")
        return self.page.evaluate("""
        () => {
            const result = {
                components: [],
                bindings: [],
                directives: []
            };
            
            // Find Angular components by looking for elements with component attributes
            const componentAttrs = [
                'ng-controller', 
                'ng-model', 
                'ng-repeat', 
                'ng-if', 
                'ng-show', 
                'ng-hide', 
                'formGroup',
                'formControlName',
                'formControl',
                'ngModel',
                'ngIf',
                'ngFor',
                'ngSwitch',
                'ngClass',
                'ngStyle',
                'routerLink'
            ];
            
            // Function to get attributes of an element
            const getAttributes = (element) => {
                const attributes = {};
                for (const attr of element.attributes) {
                    attributes[attr.name] = attr.value;
                }
                return attributes;
            };
            
            // Find all elements with Angular attributes
            document.querySelectorAll('*').forEach(element => {
                const attributes = getAttributes(element);
                
                // Check if any Angular attribute is present
                for (const attr of componentAttrs) {
                    if (attr in attributes) {
                        const rect = element.getBoundingClientRect();
                        result.components.push({
                            tagName: element.tagName.toLowerCase(),
                            selector: (element.id ? `#${element.id}` : null) || 
                                     (element.className ? `.${element.className.replace(/\\s+/g, '.')}` : null) ||
                                     element.tagName.toLowerCase(),
                            attribute: attr,
                            value: attributes[attr],
                            text: element.textContent?.trim().substring(0, 100) || null,
                            position: {
                                x: Math.round(rect.x),
                                y: Math.round(rect.y),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height)
                            }
                        });
                        break;
                    }
                }
            });
            
            // Find Angular bindings ({{ expression }})
            const treeWalker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_TEXT,
                { 
                    acceptNode: node => 
                        /\\{\\{(.+?)\\}\\}/.test(node.nodeValue) 
                        ? NodeFilter.FILTER_ACCEPT 
                        : NodeFilter.FILTER_REJECT 
                }
            );
            
            while (treeWalker.nextNode()) {
                const node = treeWalker.currentNode;
                const parent = node.parentElement;
                const matches = node.nodeValue.match(/\\{\\{(.+?)\\}\\}/g);
                
                if (matches && parent) {
                    const rect = parent.getBoundingClientRect();
                    
                    for (const match of matches) {
                        result.bindings.push({
                            binding: match,
                            expression: match.slice(2, -2).trim(),
                            parentTag: parent.tagName.toLowerCase(),
                            parentSelector: (parent.id ? `#${parent.id}` : null) || 
                                          (parent.className ? `.${parent.className.replace(/\\s+/g, '.')}` : null) ||
                                          parent.tagName.toLowerCase(),
                            position: {
                                x: Math.round(rect.x),
                                y: Math.round(rect.y),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height)
                            }
                        });
                    }
                }
            }
            
            return result;
        }
        """)
    
    def _detect_react_elements(self):
        """
        Detect and extract React-specific elements and props
        
        Returns:
            Dictionary of React elements and components
        """
        print("Detecting React elements...")
        return self.page.evaluate("""
        () => {
            const result = {
                components: [],
                props: []
            };
            
            // Look for React-specific attributes and properties
            const reactAttrs = [
                'data-reactid',
                'data-react-checksum',
                'data-reactroot',
                'data-react-helmet',
                'class', // Check for dynamic class names with common React patterns
                'id' // Check for dynamic IDs with common React patterns
            ];
            
            // Function to check if a className follows React's conventions
            const isReactClass = (className) => {
                if (!className) return false;
                
                // React often uses camelCase, BEM-style, or hash-suffixed class names
                const reactPatterns = [
                    /^[a-z][a-zA-Z0-9]+[A-Z]/, // camelCase 
                    /^[A-Z][a-zA-Z0-9]+/, // PascalCase component
                    /^[a-z][a-zA-Z0-9]+(_|-)[a-z][a-zA-Z0-9]+/, // BEM-style
                    /[a-zA-Z0-9]+(-|_)[a-z0-9]{5,}$/, // Hash suffixes
                    /^jsx-[a-zA-Z0-9]+/ // JSX-generated
                ];
                
                return reactPatterns.some(pattern => pattern.test(className));
            };
            
            // Find all elements with possible React attributes
            document.querySelectorAll('*').forEach(element => {
                const attributes = {};
                let isReactElement = false;
                
                for (const attr of element.attributes) {
                    attributes[attr.name] = attr.value;
                    
                    // Check for known React-specific attributes
                    if (attr.name.startsWith('data-react') || attr.name === 'data-reactroot') {
                        isReactElement = true;
                    }
                }
                
                // Check class names for React patterns
                if (element.className && typeof element.className === 'string') {
                    const classes = element.className.split(' ');
                    if (classes.some(isReactClass)) {
                        isReactElement = true;
                    }
                }
                
                if (isReactElement) {
                    const rect = element.getBoundingClientRect();
                    result.components.push({
                        tagName: element.tagName.toLowerCase(),
                        className: element.className,
                        id: element.id,
                        selector: (element.id ? `#${element.id}` : null) || 
                                 (element.className ? `.${element.className.replace(/\\s+/g, '.')}` : null) ||
                                 element.tagName.toLowerCase(),
                        attributes,
                        text: element.textContent?.trim().substring(0, 100) || null,
                        position: {
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        }
                    });
                }
            });
            
            return result;
        }
        """)
    
    def _detect_form_elements(self):
        """
        Advanced detection of form elements, validations, and relationships
        
        Returns:
            Dictionary of detailed form information
        """
        print("Detecting form elements and validation rules...")
        return self.page.evaluate("""
        () => {
            const result = {
                forms: [],
                formGroups: [],
                validation: []
            };
            
            // Process all forms on the page
            document.querySelectorAll('form').forEach(form => {
                const formRect = form.getBoundingClientRect();
                const formData = {
                    id: form.id,
                    name: form.getAttribute('name'),
                    action: form.getAttribute('action'),
                    method: form.getAttribute('method') || 'get',
                    enctype: form.getAttribute('enctype'),
                    selector: form.id ? `#${form.id}` : `form[name="${form.getAttribute('name') || ''}"]`,
                    position: {
                        x: Math.round(formRect.x),
                        y: Math.round(formRect.y),
                        width: Math.round(formRect.width),
                        height: Math.round(formRect.height)
                    },
                    fields: [],
                    buttons: []
                };
                
                // Process all form fields
                form.querySelectorAll('input, select, textarea').forEach(field => {
                    // Skip submit/button inputs as they'll be processed separately
                    if (field.tagName === 'INPUT' && 
                       (field.type === 'submit' || field.type === 'button' || field.type === 'reset')) {
                        return;
                    }
                    
                    const fieldRect = field.getBoundingClientRect();
                    
                    // Get associated label
                    let labelText = null;
                    let explicitLabel = null;
                    
                    if (field.id) {
                        explicitLabel = document.querySelector(`label[for="${field.id}"]`);
                        if (explicitLabel) {
                            labelText = explicitLabel.textContent.trim();
                        }
                    }
                    
                    // If no explicit label, check for wrapping label
                    if (!labelText) {
                        let parent = field.parentElement;
                        while (parent && parent !== form) {
                            if (parent.tagName === 'LABEL') {
                                labelText = parent.textContent.trim()
                                    .replace(field.value || '', '') // Remove field value from label text
                                    .trim();
                                break;
                            }
                            parent = parent.parentElement;
                        }
                    }
                    
                    // Get validation attributes
                    const validationAttrs = [
                        'required', 'pattern', 'min', 'max', 'minlength', 'maxlength',
                        'step', 'data-validate', 'aria-required'
                    ];
                    
                    const validation = {};
                    let hasValidation = false;
                    
                    validationAttrs.forEach(attr => {
                        if (field.hasAttribute(attr)) {
                            validation[attr] = field.getAttribute(attr);
                            hasValidation = true;
                        }
                    });
                    
                    // Check for HTML5 validation types
                    if (['email', 'url', 'number', 'tel', 'date'].includes(field.type)) {
                        validation.type = field.type;
                        hasValidation = true;
                    }
                    
                    // If field has validation, add to the validation array
                    if (hasValidation) {
                        result.validation.push({
                            field: field.name || field.id,
                            selector: field.id ? `#${field.id}` : `[name="${field.name}"]`,
                            validation
                        });
                    }
                    
                    formData.fields.push({
                        type: field.type || field.tagName.toLowerCase(),
                        name: field.name,
                        id: field.id,
                        value: field.value,
                        placeholder: field.placeholder,
                        label: labelText,
                        required: field.required,
                        disabled: field.disabled,
                        readonly: field.readOnly,
                        validation: hasValidation ? validation : null,
                        selector: field.id ? `#${field.id}` : `[name="${field.name}"]`,
                        position: {
                            x: Math.round(fieldRect.x),
                            y: Math.round(fieldRect.y),
                            width: Math.round(fieldRect.width),
                            height: Math.round(fieldRect.height)
                        }
                    });
                });
                
                // Process form buttons
                form.querySelectorAll('button, input[type="submit"], input[type="button"], input[type="reset"]').forEach(button => {
                    const buttonRect = button.getBoundingClientRect();
                    
                    formData.buttons.push({
                        type: button.type || (button.tagName === 'BUTTON' ? 'submit' : 'button'),
                        name: button.name,
                        id: button.id,
                        value: button.value,
                        text: button.textContent || button.value,
                        selector: button.id ? `#${button.id}` : (button.name ? `[name="${button.name}"]` : button.tagName.toLowerCase()),
                        position: {
                            x: Math.round(buttonRect.x),
                            y: Math.round(buttonRect.y),
                            width: Math.round(buttonRect.width),
                            height: Math.round(buttonRect.height)
                        }
                    });
                });
                
                result.forms.push(formData);
            });
            
            // Look for form groups (like divs with form-group class, fieldsets, etc.)
            document.querySelectorAll('.form-group, fieldset, .form-field, .form-row, .input-group').forEach(group => {
                const groupRect = group.getBoundingClientRect();
                
                // Get all form controls in this group
                const controls = Array.from(group.querySelectorAll('input, select, textarea'))
                    .filter(el => {
                        // Skip hidden, button and submit types
                        return el.type !== 'hidden' && 
                               el.type !== 'submit' && 
                               el.type !== 'button' &&
                               el.type !== 'reset';
                    });
                
                if (controls.length === 0) return;
                
                // Get the group label (legend, label, or heading)
                const labelElement = group.querySelector('legend, label, h1, h2, h3, h4, h5, h6, [aria-label]');
                const label = labelElement ? labelElement.textContent.trim() : null;
                
                result.formGroups.push({
                    type: group.tagName.toLowerCase(),
                    className: group.className,
                    id: group.id,
                    label,
                    controlCount: controls.length,
                    controls: controls.map(control => ({
                        type: control.type || control.tagName.toLowerCase(),
                        name: control.name,
                        id: control.id,
                        selector: control.id ? `#${control.id}` : (control.name ? `[name="${control.name}"]` : control.tagName.toLowerCase())
                    })),
                    selector: group.id ? `#${group.id}` : (group.className ? `.${group.className.split(' ')[0]}` : group.tagName.toLowerCase()),
                    position: {
                        x: Math.round(groupRect.x),
                        y: Math.round(groupRect.y),
                        width: Math.round(groupRect.width),
                        height: Math.round(groupRect.height)
                    }
                });
            });
            
            return result;
        }
        """)
    
    def _detect_accessible_elements(self):
        """
        Detect elements with accessibility attributes and ARIA roles
        
        Returns:
            Dictionary of accessible elements
        """
        print("Detecting accessibility features and issues...")
        return self.page.evaluate("""
        () => {
            const result = {
                ariaElements: [],
                landmarks: [],
                accessibilityIssues: []
            };
            
            // ARIA attributes to look for
            const ariaAttrs = [
                'aria-label', 'aria-labelledby', 'aria-describedby', 'aria-description',
                'aria-hidden', 'aria-expanded', 'aria-haspopup', 'aria-controls',
                'aria-owns', 'aria-live', 'aria-atomic', 'aria-relevant', 
                'aria-disabled', 'aria-checked', 'aria-pressed', 'aria-selected',
                'aria-invalid', 'aria-required', 'aria-multiline', 'aria-multiselectable',
                'aria-orientation', 'aria-sort', 'aria-valuemin', 'aria-valuemax',
                'aria-valuenow', 'aria-valuetext', 'aria-busy', 'aria-dropeffect',
                'aria-grabbed', 'aria-activedescendant', 'aria-colcount', 'aria-colindex',
                'aria-colspan', 'aria-rowcount', 'aria-rowindex', 'aria-rowspan'
            ];
            
            // Landmark roles
            const landmarkRoles = [
                'banner', 'complementary', 'contentinfo', 'form', 'main', 
                'navigation', 'region', 'search'
            ];
            
            // Process all elements with ARIA attributes
            document.querySelectorAll('[role], [aria-label], [aria-labelledby], [aria-describedby]').forEach(element => {
                const role = element.getAttribute('role');
                const rect = element.getBoundingClientRect();
                
                // Check if element has any ARIA attribute
                const ariaAttributes = {};
                let hasAriaAttr = false;
                
                for (const attr of ariaAttrs) {
                    if (element.hasAttribute(attr)) {
                        ariaAttributes[attr] = element.getAttribute(attr);
                        hasAriaAttr = true;
                    }
                }
                
                if (role || hasAriaAttr) {
                    const elementData = {
                        tagName: element.tagName.toLowerCase(),
                        role,
                        id: element.id,
                        ariaAttributes,
                        text: element.textContent?.trim().substring(0, 100) || null,
                        selector: element.id ? `#${element.id}` : `[role="${role}"]`,
                        position: {
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        }
                    };
                    
                    result.ariaElements.push(elementData);
                    
                    // Check if it's a landmark
                    if (role && landmarkRoles.includes(role)) {
                        result.landmarks.push(elementData);
                    }
                }
            });
            
            // Check for common accessibility issues
            
            // 1. Images without alt text
            document.querySelectorAll('img:not([alt])').forEach(img => {
                const rect = img.getBoundingClientRect();
                
                result.accessibilityIssues.push({
                    type: 'missing-alt',
                    element: 'img',
                    selector: img.id ? `#${img.id}` : (img.src ? `img[src*="${img.src.split('/').pop()}"]` : 'img'),
                    position: {
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    }
                });
            });
            
            // 2. Links without text
            document.querySelectorAll('a').forEach(link => {
                if (!link.textContent.trim() && !link.getAttribute('aria-label') && !link.querySelector('img[alt]')) {
                    const rect = link.getBoundingClientRect();
                    
                    result.accessibilityIssues.push({
                        type: 'empty-link',
                        element: 'a',
                        href: link.href,
                        selector: link.id ? `#${link.id}` : (link.href ? `a[href*="${link.href.split('/').pop()}"]` : 'a'),
                        position: {
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        }
                    });
                }
            });
            
            // 3. Form fields without labels
            document.querySelectorAll('input, select, textarea').forEach(field => {
                if (field.type === 'hidden' || field.type === 'submit' || field.type === 'button' || field.type === 'reset') {
                    return;
                }
                
                let hasLabel = false;
                
                // Check for explicit label
                if (field.id && document.querySelector(`label[for="${field.id}"]`)) {
                    hasLabel = true;
                }
                
                // Check for wrapping label
                if (!hasLabel) {
                    let parent = field.parentElement;
                    while (parent && parent.tagName !== 'FORM') {
                        if (parent.tagName === 'LABEL') {
                            hasLabel = true;
                            break;
                        }
                        parent = parent.parentElement;
                    }
                }
                
                // Check for aria-label or aria-labelledby
                if (!hasLabel && (field.hasAttribute('aria-label') || field.hasAttribute('aria-labelledby'))) {
                    hasLabel = true;
                }
                
                if (!hasLabel) {
                    const rect = field.getBoundingClientRect();
                    
                    result.accessibilityIssues.push({
                        type: 'missing-label',
                        element: field.tagName.toLowerCase(),
                        name: field.name,
                        id: field.id,
                        selector: field.id ? `#${field.id}` : (field.name ? `[name="${field.name}"]` : field.tagName.toLowerCase()),
                        position: {
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        }
                    });
                }
            });
            
            return result;
        }
        """)
    
    def _detect_dynamic_content(self):
        """
        Detect potentially dynamic content areas and AJAX interactions
        
        Returns:
            Dictionary of dynamic content areas
        """
        print("Detecting dynamic content areas...")
        return self.page.evaluate("""
        () => {
            const result = {
                dynamicAreas: [],
                eventHandlers: [],
                ajaxElements: []
            };
            
            // Class names that often indicate dynamic content
            const dynamicClassPatterns = [
                'dynamic', 'ajax', 'lazy', 'load', 'update', 'refresh', 'live',
                'content', 'data', 'feed', 'stream', 'widget', 'module', 'component',
                'carousel', 'slider', 'toggle', 'tab', 'accordion', 'dropdown'
            ];
            
            // ID patterns that often indicate dynamic content
            const dynamicIdPatterns = [
                'dynamic', 'ajax', 'live', 'update', 'content', 'data', 'feed', 
                'stream', 'widget', 'container', 'wrapper', 'results'
            ];
            
            // Find elements that might contain dynamic content
            document.querySelectorAll('*').forEach(element => {
                let isDynamic = false;
                let dynamicReason = [];
                
                // Check class names
                if (element.className && typeof element.className === 'string') {
                    const classes = element.className.toLowerCase().split(' ');
                    for (const pattern of dynamicClassPatterns) {
                        if (classes.some(cls => cls.includes(pattern))) {
                            isDynamic = true;
                            dynamicReason.push(`class contains "${pattern}"`);
                            break;
                        }
                    }
                }
                
                // Check ID
                if (element.id) {
                    const id = element.id.toLowerCase();
                    for (const pattern of dynamicIdPatterns) {
                        if (id.includes(pattern)) {
                            isDynamic = true;
                            dynamicReason.push(`id contains "${pattern}"`);
                            break;
                        }
                    }
                }
                
                // Check for data attributes related to dynamic content
                for (const attr of element.attributes) {
                    if (attr.name.startsWith('data-') && 
                       (attr.name.includes('load') || 
                        attr.name.includes('url') || 
                        attr.name.includes('src') || 
                        attr.name.includes('ajax') || 
                        attr.name.includes('dynamic') || 
                        attr.name.includes('bind') || 
                        attr.name.includes('template'))) {
                        isDynamic = true;
                        dynamicReason.push(`has "${attr.name}" attribute`);
                    }
                }
                
                // Add to result if it seems to be dynamic
                if (isDynamic) {
                    const rect = element.getBoundingClientRect();
                    
                    result.dynamicAreas.push({
                        tagName: element.tagName.toLowerCase(),
                        id: element.id,
                        className: element.className,
                        selector: element.id ? `#${element.id}` : (element.className ? `.${element.className.split(' ')[0]}` : element.tagName.toLowerCase()),
                        reason: dynamicReason,
                        position: {
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        }
                    });
                }
            });
            
            // Find elements with event listeners (approximate approach as we can't directly access all attached listeners)
            const commonInteractiveElements = 'a, button, input, select, textarea, [role="button"], [role="link"], [role="checkbox"], [role="radio"], [role="tab"], [role="menuitem"], [tabindex]';
            
            document.querySelectorAll(commonInteractiveElements).forEach(element => {
                // Check for inline event handlers
                const eventHandlers = {};
                let hasHandlers = false;
                
                for (const attr of element.attributes) {
                    if (attr.name.startsWith('on')) {
                        eventHandlers[attr.name] = attr.value;
                        hasHandlers = true;
                    }
                }
                
                if (hasHandlers) {
                    const rect = element.getBoundingClientRect();
                    
                    result.eventHandlers.push({
                        tagName: element.tagName.toLowerCase(),
                        id: element.id,
                        text: element.textContent?.trim().substring(0, 100) || element.value,
                        handlers: eventHandlers,
                        selector: element.id ? `#${element.id}` : (element.className ? `.${element.className.split(' ')[0]}` : element.tagName.toLowerCase()),
                        position: {
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        }
                    });
                }
            });
            
            // Look for AJAX indicators
            document.querySelectorAll('[data-url], [data-src], [data-ajax], [data-remote], .ajax-load, .ajax-content, .load-more, .infinite-scroll, [data-load]').forEach(element => {
                const rect = element.getBoundingClientRect();
                
                result.ajaxElements.push({
                    tagName: element.tagName.toLowerCase(),
                    id: element.id,
                    className: element.className,
                    attributes: Array.from(element.attributes).reduce((obj, attr) => {
                        obj[attr.name] = attr.value;
                        return obj;
                    }, {}),
                    selector: element.id ? `#${element.id}` : (element.className ? `.${element.className.split(' ')[0]}` : element.tagName.toLowerCase()),
                    position: {
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    }
                });
            });
            
            return result;
        }
        """)
    
    def _generate_advanced_descriptors(self):
        """
        Generate more comprehensive element descriptors for advanced use cases
        Combines information from standard analysis and framework-specific detection
        """
        print("Generating advanced element descriptors...")
        if not self.elements_data or not self.output_dir:
            print("Error: Element data or output directory not available for generating advanced descriptors.")
            return
            
        descriptors = []
        
        # Process elements by category
        for category, elements in self.elements_data.items():
            if not isinstance(elements, list):
                continue
                
            for element in elements:
                if not isinstance(element, dict) or not element.get("selectors", {}).get("css"):
                    continue
                
                # Create a clean name for the element
                name = element.get("name", "")
                if not name:
                    # Try to create a name from description or text
                    name = element.get("description", "").split(":")[0] or element.get("text", "")
                    if not name:
                        # Use tagName and category as fallback
                        name = f"{element.get('tagName', '')}_{category}"
                
                # Clean the name
                name = ''.join(c if c.isalnum() else '_' for c in name.lower())
                name = '_'.join(filter(None, name.split('_')))  # Remove empty parts
                
                # Create the descriptor
                descriptor = {
                    "name": name,
                    "description": element.get("description", ""),
                    "category": category,
                    "selectors": {
                        "css": element.get("selectors", {}).get("css", ""),
                        "xpath": element.get("selectors", {}).get("xpath", ""),
                        "accessibility": element.get("selectors", {}).get("accessibility", "")
                    },
                    "properties": {
                        "tagName": element.get("tagName", ""),
                        "text": element.get("text", ""),
                        "attributes": element.get("attributes", {}),
                        "position": element.get("position", {})
                    },
                    "is_visible": element.get("isVisible", True)
                }
                
                # Add framework-specific information if available
                if self.framework_data:
                    # Add React component info
                    if self.framework_data.get("react") and self.framework_data["react"].get("components"):
                        for component in self.framework_data["react"]["components"]:
                            if (component.get("id") == element.get("attributes", {}).get("id") or
                                component.get("selector") == element.get("selectors", {}).get("css")):
                                descriptor["framework"] = {
                                    "type": "React",
                                    "component": component.get("className", ""),
                                    "props": component.get("attributes", {})
                                }
                    
                    # Add Angular info
                    if self.framework_data.get("angular") and self.framework_data["angular"].get("components"):
                        for component in self.framework_data["angular"]["components"]:
                            if component.get("selector") == element.get("selectors", {}).get("css"):
                                descriptor["framework"] = {
                                    "type": "Angular",
                                    "directive": component.get("attribute", ""),
                                    "binding": component.get("value", "")
                                }
                
                descriptors.append(descriptor)
        
        # Save to file
        if descriptors:
            try:
                descriptors_path = os.path.join(self.output_dir, "advanced_descriptors.json")
                with open(descriptors_path, "w", encoding="utf-8") as f:
                    json.dump(descriptors, f, indent=2)
                print(f"Generated {len(descriptors)} advanced element descriptors")
            except Exception as e:
                print(f"Error saving advanced descriptors: {e}")
        else:
            print("No elements found for advanced descriptors") 