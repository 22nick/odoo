/** @odoo-module **/

// Helper function to get tool icons
export function getToolIcon(tool) {
    const icons = {
        'select': 'fa fa-mouse-pointer  me-1',
        'rectangle': 'fa fa-square  me-1',
        'circle': 'fa fa-circle  me-1',
        'ellipse': 'fa fa-circle-o  me-1' , // Outline circle for ellipse
        'line': 'fa fa-minus  me-1',
        'text': 'fa fa-font  me-1',
        'path': 'fa fa-pencil  me-1', // Changed from paint-brush for better clarity
        'lshape': 'fa fa-cube me-1'
    };
    return icons[tool] || 'fa fa-question';
}

// SVG Element Factory for creating and updating elements
export class SvgElementFactory {
    /**
     * Creates a new SVG element object.
     * @param {string} type - The type of SVG element (e.g., 'rect', 'circle').
     * @param {{x: number, y: number}} startPoint - The initial SVG coordinates.
     * @param {object} attributes - Additional attributes for the element.
     * @returns {object | null} The new SVG element object or null if type is unsupported.
     */
    static createElement(type, startPoint, attributes = {}) {
        const id = `element_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const baseAttributes = {
            fill: 'none',
            stroke: '#000000',
            'stroke-width': '2',
            rotation: 0,
            ...attributes
        };
        console.log("startPoint")
        console.log(startPoint)
        switch (type) {
            case 'rectangle':
                return {
                    id,
                    type: 'rect',
                    attributes: {
                        ...baseAttributes,
                        x: startPoint.x,
                        y: startPoint.y,
                        width: 0,
                        height: 0,
                        rx: 0,
                        ry: 0
                    }
                };
            case 'circle':
                return {
                    id,
                    type: 'circle',
                    attributes: {
                        ...baseAttributes,
                        cx: startPoint.x,
                        cy: startPoint.y,
                        r: 0
                    }
                };
            case 'ellipse':
                return {
                    id,
                    type: 'ellipse',
                    attributes: {
                        ...baseAttributes,
                        cx: startPoint.x,
                        cy: startPoint.y,
                        rx: 0,
                        ry: 0
                    }
                };
            case 'line':
                return {
                    id,
                    type: 'line',
                    attributes: {
                        ...baseAttributes,
                        x1: startPoint.x,
                        y1: startPoint.y,
                        x2: startPoint.x,
                        y2: startPoint.y
                    }
                };
            case 'text':
                return {
                    id,
                    type: 'text',
                    attributes: {
                        ...baseAttributes,
                        x: startPoint.x,
                        y: startPoint.y,
                        fill: '#000000',
                        'font-size': '16',
                        'font-family': 'Arial, sans-serif'
                    },
                    textContent: 'Text' // Initial text content
                };
            case 'path':
                 return {
                    id,
                    type: 'path',
                    attributes: {
                        ...baseAttributes,
                        d: `M${startPoint.x},${startPoint.y}`
                    },
                };
            default:
                return null;
        }
    }

    /**
     * Updates an element's dimensions during drawing based on start and current points.
     * @param {object} element - The SVG element object to update.
     * @param {{x: number, y: number}} startPoint - The initial mouse down point.
     * @param {{x: number, y: number}} currentPoint - The current mouse position.
     * @param {boolean} shiftKey - True if Shift key is pressed for constraints.
     */
    static updateElement(element, startPoint, currentPoint, shiftKey = false) {
        const { x: startX, y: startY } = startPoint;
        const { x: currentX, y: currentY } = currentPoint;

        switch (element.type) {
            case 'rect':
                element.attributes.x = Math.min(startX, currentX);
                element.attributes.y = Math.min(startY, currentY);
                element.attributes.width = Math.abs(currentX - startX);
                element.attributes.height = Math.abs(currentY - startY);

                // Square mode with shift key
                if (shiftKey) {
                    const size = Math.max(element.attributes.width, element.attributes.height);
                    element.attributes.width = size;
                    element.attributes.height = size;
                    // Adjust x/y to keep start corner fixed
                    element.attributes.x = startX < currentX ? startX : startX - size;
                    element.attributes.y = startY < currentY ? startY : startY - size;
                }
                break;

            case 'circle':
                const radius = Math.sqrt(Math.pow(currentX - startX, 2) + Math.pow(currentY - startY, 2));
                element.attributes.cx = startX;
                element.attributes.cy = startY;
                element.attributes.r = radius;
                break;

            case 'ellipse':
                element.attributes.cx = startX;
                element.attributes.cy = startY;
                element.attributes.rx = Math.abs(currentX - startX);
                element.attributes.ry = Math.abs(currentY - startY);

                // Circle mode with shift key
                if (shiftKey) {
                    const minRadius = Math.max(element.attributes.rx, element.attributes.ry);
                    element.attributes.rx = minRadius;
                    element.attributes.ry = minRadius;
                }
                break;

            case 'line':
                element.attributes.x1 = startX;
                element.attributes.y1 = startY;
                element.attributes.x2 = currentX;
                element.attributes.y2 = currentY;

                // Constrain to 45-degree angles with shift key
                if (shiftKey) {
                    const deltaX = currentX - startX;
                    const deltaY = currentY - startY;
                    const angle = Math.atan2(deltaY, deltaX);
                    // Snap to nearest 45-degree increment
                    const constrainedAngle = Math.round(angle / (Math.PI / 4)) * (Math.PI / 4);
                    const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

                    element.attributes.x2 = startX + Math.cos(constrainedAngle) * distance;
                    element.attributes.y2 = startY + Math.sin(constrainedAngle) * distance;
                }
                break;

             case 'path':
                // For path, we only add points on mousemove if it's the initial drag.
                // Assuming simple freehand path where mousemove adds points.
                const lastPointMatch = element.attributes.d.match(/L(\d+\.?\d*),(\d+\.?\d*)$/);
                let lastPathX = startX;
                let lastPathY = startY;
                if (lastPointMatch) {
                    lastPathX = parseFloat(lastPointMatch[1]);
                    lastPathY = parseFloat(lastPointMatch[2]);
                }

                const dist = Math.sqrt(Math.pow(currentX - lastPathX, 2) + Math.pow(currentY - lastPathY, 2));
                if (dist > 5) { // Only add point if moved more than 5 pixels
                    element.attributes.d += ` L${currentX},${currentY}`;
                }
                break;
        }
    }

/**
     * Updates the L-shape (polyline) path as the user draws it.
     * It creates alternating horizontal and vertical segments.
     * @param {object} element - The path element for the L-shape.
     * @param {Array<{x, y}>} points - The array of clicked corner points.
     * @param {{x, y}} [currentPoint] - The current mouse position for live preview. If null, finalizes the path.
     */
    static updateLShape(element, points, currentPoint) {
        if (!element || points.length === 0) return;

        let d = `M${points[0].x},${points[0].y}`;
        let lastPoint = points[0];

        // Draw the fixed segments based on the clicked points
        for (let i = 1; i < points.length; i++) {
            d += ` L${points[i].x},${points[i].y}`;
            lastPoint = points[i];
        }

        // Draw the live preview segment if the mouse is moving
        if (currentPoint) {
            // Determine if the next segment should be horizontal or vertical
            // The number of segments is points.length - 1. We check the orientation of the *next* segment.
            if (points.length % 2 !== 0) { // Odd number of points means the next segment is horizontal
                d += ` L${currentPoint.x},${lastPoint.y}`;
            } else { // Even number of points means the next segment is vertical
                d += ` L${lastPoint.x},${currentPoint.y}`;
            }
        }
        element.attributes.d = d;
    }


    /**
     * Moves an existing SVG element by a given delta.
     * @param {object} element - The SVG element object to move.
     * @param {number} dx - Change in X coordinate.
     * @param {number} dy - Change in Y coordinate.
     */
    static moveElement(element, dx, dy) {
       const transform = element.attributes.transform || '';
        let rotate = '';
        let translate = { x: 0, y: 0 };

        const rotateMatch = transform.match(/rotate\([^)]+\)/);
        if (rotateMatch) {
            rotate = rotateMatch[0];
        }

        const translateMatch = transform.match(/translate\(([^,]+),([^)]+)\)/);
        if (translateMatch) {
            translate.x = parseFloat(translateMatch[1]);
            translate.y = parseFloat(translateMatch[2]);
        }

        // This is the fix: Apply the delta to the existing translation
        translate.x += dx;
        translate.y += dy;

        element.attributes.transform = `translate(${translate.x}, ${translate.y}) ${rotate}`;
    }

    /**
     * Resizes an existing SVG element based on a handle and current mouse position.
     * @param {object} element - The SVG element object to resize.
     * @param {string} handle - The name of the resize handle ('nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w').
     * @param {{x: number, y: number}} startPoint - The initial mouse down point (opposite handle).
     * @param {{x: number, y: number}} currentPoint - The current mouse position.
     * @param {boolean} shiftKey - True if Shift key is pressed for aspect ratio constraint.
     */
    static resizeElement(element, handle, startPoint, currentPoint, shiftKey = false) {
        const { x: startX, y: startY } = startPoint;
        const { x: currentX, y: currentY } = currentPoint;

        switch (element.type) {
            case 'rect':
                let newX = parseFloat(element.attributes.x);
                let newY = parseFloat(element.attributes.y);
                let newWidth = parseFloat(element.attributes.width);
                let newHeight = parseFloat(element.attributes.height);

                if (handle.includes('e')) { // East handles
                    newWidth = currentX - newX;
                } else if (handle.includes('w')) { // West handles
                    newWidth = newX + newWidth - currentX;
                    newX = currentX;
                }
                if (handle.includes('s')) { // South handles
                    newHeight = currentY - newY;
                } else if (handle.includes('n')) { // North handles
                    newHeight = newY + newHeight - currentY;
                    newY = currentY;
                }

                // Constrain aspect ratio with Shift key
                if (shiftKey) {
                    const originalAspectRatio = parseFloat(element.attributes.width) / parseFloat(element.attributes.height);
                    if (handle.includes('e') || handle.includes('w')) { // Horizontal drag
                        newHeight = newWidth / originalAspectRatio;
                    } else { // Vertical drag
                        newWidth = newHeight * originalAspectRatio;
                    }
                    // Re-adjust x/y if resizing from top/left to maintain fixed opposite corner
                    if (handle.includes('w')) newX = startX - newWidth;
                    if (handle.includes('n')) newY = startY - newHeight;
                }

                element.attributes.x = newX;
                element.attributes.y = newY;
                element.attributes.width = Math.max(0, newWidth); // Ensure non-negative dimensions
                element.attributes.height = Math.max(0, newHeight);
                break;

            case 'circle':
                // Resize based on distance from center (cx, cy) to current point
                const cx = parseFloat(element.attributes.cx);
                const cy = parseFloat(element.attributes.cy);
                element.attributes.r = Math.sqrt(Math.pow(currentX - cx, 2) + Math.pow(currentY - cy, 2));
                break;

            case 'ellipse':
                // Resize rx/ry based on distance from center (cx, cy)
                const ecx = parseFloat(element.attributes.cx);
                const ecy = parseFloat(element.attributes.cy);
                element.attributes.rx = Math.abs(currentX - ecx);
                element.attributes.ry = Math.abs(currentY - ecy);
                if (shiftKey) { // Constrain to circle
                    const minRadius = Math.max(element.attributes.rx, element.attributes.ry);
                    element.attributes.rx = minRadius;
                    element.attributes.ry = minRadius;
                }
                break;

            case 'line':
                // Lines are resized by moving one of their endpoints (x1,y1 or x2,y2)
                // The handle indicates which endpoint is being moved.
                if (handle === 'start') { // Assuming a 'start' handle for x1,y1
                    element.attributes.x1 = currentX;
                    element.attributes.y1 = currentY;
                } else if (handle === 'end') { // Assuming an 'end' handle for x2,y2
                    element.attributes.x2 = currentX;
                    element.attributes.y2 = currentY;
                }
                // If no specific handle (e.g., center handles on a line), treat as moving both ends proportionally
                // This would require more complex logic. For now, only corner/end handles are supported.
                break;

            case 'text':
                // Text elements are typically resized by changing font-size.
                // This would involve calculating a new font-size based on drag.
                // For simplicity, we'll just allow moving for now. Resizing text visually
                // with handles is more complex as it affects font-size directly.
                // A simpler approach is to only allow font-size changes via properties panel.
                break;

            case 'path':
                // Resizing a path is highly complex as it involves scaling all points in 'd'.
                // For now, paths are not directly resizable via handles, only movable.
                break;
        }
        this.applyRotation(element);
    }
    /**
     * Rotates an element based on the current mouse position.
     * @param {object} element - The SVG element to rotate.
     * @param {{x: number, y: number}} currentPoint - The current mouse position.
     */
    static rotateElement(element, currentPoint) {
        const bounds = getElementBounds(element, false); // Get unrotated bounds for center
        if (!bounds) return;

        const centerX = bounds.cx;
        const centerY = bounds.cy;
        const angle = Math.atan2(currentPoint.y - centerY, currentPoint.x - centerX) * (180 / Math.PI);

        element.attributes.rotation = angle.toFixed(2);
        this.applyRotation(element);
    }
    /**
     * Applies the rotation transform to an element.
     * @param {object} element - The SVG element.
     */
    static applyRotation(element) {
        const rotation = element.attributes.rotation || 0;
        const bounds = getElementBounds(element, false);
        if (!bounds) return;

        const centerX = bounds.cx;
        const centerY = bounds.cy;

        const transform = element.attributes.transform || '';
        const translateMatch = transform.match(/translate\([^)]+\)/);
        const translate = translateMatch ? translateMatch[0] : '';

        element.attributes.transform = `${translate} rotate(${rotation}, ${centerX}, ${centerY})`;
    }
}

// SVG Export Utility
export class SvgExporter {
    /**
     * Generates the full SVG content string from elements and canvas settings.
     * @param {Array<object>} elements - Array of SVG element objects.
     * @param {number} canvasWidth - Width of the SVG canvas.
     * @param {number} canvasHeight - Height of the SVG canvas.
     * @param {string} backgroundColor - Background color of the SVG.
     * @returns {string} The complete SVG XML string.
     */
    static generateSvgContent(elements, canvasWidth, canvasHeight, backgroundColor) {
        const elementStrings = elements.map(el => {
            const attrs = Object.entries(el.attributes)
                .map(([key, value]) => `${key}="${value}"`)
                .join(' ');

            if (el.type === 'text') {
                return `<${el.type} ${attrs}>${el.textContent || ''}</${el.type}>`;
            } else {
                return `<${el.type} ${attrs} />`;
            }
        }).join('\n    ');

        return `<?xml version="1.0" encoding="UTF-8"?>
<svg width="${canvasWidth}" height="${canvasHeight}" xmlns="http://www.w3.org/2000/svg" style="background-color: ${backgroundColor}">
    ${elementStrings}
</svg>`;
    }

    /**
     * Exports SVG content as an SVG file for download.
     * @param {string} svgContent - The SVG XML string.
     * @param {string} filename - The desired filename.
     */
    static exportAsFile(svgContent, filename = 'drawing.svg') {
        const blob = new Blob([svgContent], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    /**
     * Exports SVG content as a PNG image for download.
     * @param {string} svgContent - The SVG XML string.
     * @param {number} canvasWidth - Width of the canvas for PNG export.
     * @param {number} canvasHeight - Height of the canvas for PNG export.
     * @param {string} filename - The desired filename.
     */
    static exportAsPng(svgContent, canvasWidth, canvasHeight, filename = 'drawing.png') {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = canvasWidth;
        canvas.height = canvasHeight;

        const img = new Image();
        const svgBlob = new Blob([svgContent], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(svgBlob);

        img.onload = function() {
            ctx.drawImage(img, 0, 0);

            canvas.toBlob(function(blob) {
                const downloadUrl = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(downloadUrl);
            }, 'image/png');

            URL.revokeObjectURL(url);
        };

        img.src = url;
    }
}

// SVG Import Utility
export class SvgImporter {
    /**
     * Parses an SVG file and returns an array of SVG element objects.
     * @param {File} file - The SVG file to parse.
     * @returns {Promise<Array<object>>} A promise that resolves with an array of SVG element objects.
     */
    static parseSvgFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = function(e) {
                try {
                    const svgContent = e.target.result;
                    const elements = SvgImporter.parseSvgContent(svgContent);
                    resolve(elements);
                } catch (error) {
                    reject(error);
                }
            };
            reader.onerror = reject;
            reader.readAsText(file);
        });
    }

    /**
     * Parses an SVG content string and returns an array of SVG element objects.
     * @param {string} svgContent - The SVG XML string.
     * @returns {Array<object>} An array of SVG element objects.
     * @throws {Error} If the SVG content is invalid.
     */
    static parseSvgContent(svgContent) {
        const parser = new DOMParser();
        const doc = parser.parseFromString(svgContent, 'image/svg+xml');
        const svg = doc.querySelector('svg');

        if (!svg) {
            throw new Error('Invalid SVG content: No <svg> element found.');
        }

        const elements = [];
        // Define supported SVG element types for import
        const supportedElements = ['rect', 'circle', 'ellipse', 'line', 'text', 'path'];

        // Iterate through all children of the SVG element
        Array.from(svg.children).forEach((el, index) => {
            if (supportedElements.includes(el.tagName)) {
                const element = {
                    id: `imported_element_${Date.now()}_${index}`, // Generate unique ID
                    type: el.tagName,
                    attributes: SvgImporter.getElementAttributes(el)
                };

                if (el.tagName === 'text') {
                    element.textContent = el.textContent || '';
                }

                elements.push(element);
            } else {
                console.warn(`Unsupported SVG element during import: <${el.tagName}>. Skipping.`);
            }
        });

        return elements;
    }

    /**
     * Extracts attributes from a DOM element into a plain object.
     * @param {Element} element - The DOM element.
     * @returns {object} An object containing the element's attributes.
     */
    static getElementAttributes(element) {
        const attrs = {};
        for (const attr of element.attributes) {
            attrs[attr.name] = attr.value;
        }
        return attrs;
    }
}

// History Manager for Undo/Redo functionality
export class HistoryManager {
    /**
     * @param {number} maxHistorySize - Maximum number of states to store in history.
     */
    constructor(maxHistorySize = 50) {
        this.history = [];
        this.currentIndex = -1;
        this.maxHistorySize = maxHistorySize;
    }

    /**
     * Adds a new state to the history.
     * @param {object} state - The state object to add (e.g., { elements: [...], selectedElementId: '...' }).
     */
    addState(state) {
        // Remove any states after current index (if undo was performed)
        this.history = this.history.slice(0, this.currentIndex + 1);

        // Add new state
        this.history.push(state);

        // Limit history size
        if (this.history.length > this.maxHistorySize) {
            this.history.shift(); // Remove oldest state
        } else {
            this.currentIndex++;
        }
    }

    /**
     * Undoes the last action by returning to the previous state.
     * @returns {object | null} The previous state object, or null if nothing to undo.
     */
    undo() {
        if (this.canUndo()) {
            this.currentIndex--;
            return this.history[this.currentIndex];
        }
        return null;
    }

    /**
     * Redoes the last undone action by returning to the next state.
     * @returns {object | null} The next state object, or null if nothing to redo.
     */
    redo() {
        if (this.canRedo()) {
            this.currentIndex++;
            return this.history[this.currentIndex];
        }
        return null;
    }

    /**
     * Checks if there are any actions to undo.
     * @returns {boolean} True if undo is possible, false otherwise.
     */
    canUndo() {
        return this.currentIndex > 0;
    }

    /**
     * Checks if there are any actions to redo.
     * @returns {boolean} True if redo is possible, false otherwise.
     */
    canRedo() {
        return this.currentIndex < this.history.length - 1;
    }

    /**
     * Clears the entire history.
     */
    clear() {
        this.history = [];
        this.currentIndex = -1;
    }
}

// Snap to Grid Utility
export class SnapToGrid {
    /**
     * Snaps a single coordinate value to the nearest grid line.
     * @param {number} value - The coordinate value.
     * @param {number} gridSize - The size of the grid cells.
     * @returns {number} The snapped coordinate value.
     */
    static snapValue(value, gridSize) {
        return Math.round(value / gridSize) * gridSize;
    }

    /**
     * Snaps a point (x, y) to the nearest grid intersection.
     * @param {{x: number, y: number}} point - The point to snap.
     * @param {number} gridSize - The size of the grid cells.
     * @returns {{x: number, y: number}} The snapped point.
     */
    static snapPoint(point, gridSize) {
        return {
            x: SnapToGrid.snapValue(point.x, gridSize),
            y: SnapToGrid.snapValue(point.y, gridSize)
        };
    }

    /**
     * Snaps an element's position/dimensions to the grid.
     * This is useful after an element has been moved/resized, to align it.
     * @param {object} element - The SVG element object to snap.
     * @param {number} gridSize - The size of the grid cells.
     * @returns {object} A new element object with snapped attributes.
     */
    static snapElement(element, gridSize) {
        const snappedElement = JSON.parse(JSON.stringify(element)); // Deep copy

        switch (snappedElement.type) {
            case 'rect':
                snappedElement.attributes.x = SnapToGrid.snapValue(snappedElement.attributes.x, gridSize);
                snappedElement.attributes.y = SnapToGrid.snapValue(snappedElement.attributes.y, gridSize);
                snappedElement.attributes.width = SnapToGrid.snapValue(snappedElement.attributes.width, gridSize);
                snappedElement.attributes.height = SnapToGrid.snapValue(snappedElement.attributes.height, gridSize);
                break;
            case 'circle':
                snappedElement.attributes.cx = SnapToGrid.snapValue(snappedElement.attributes.cx, gridSize);
                snappedElement.attributes.cy = SnapToGrid.snapValue(snappedElement.attributes.cy, gridSize);
                snappedElement.attributes.r = SnapToGrid.snapValue(snappedElement.attributes.r, gridSize);
                break;
            case 'ellipse':
                snappedElement.attributes.cx = SnapToGrid.snapValue(snappedElement.attributes.cx, gridSize);
                snappedElement.attributes.cy = SnapToGrid.snapValue(snappedElement.attributes.cy, gridSize);
                snappedElement.attributes.rx = SnapToGrid.snapValue(snappedElement.attributes.rx, gridSize);
                snappedElement.attributes.ry = SnapToGrid.snapValue(snappedElement.attributes.ry, gridSize);
                break;
            case 'line':
                snappedElement.attributes.x1 = SnapToGrid.snapValue(snappedElement.attributes.x1, gridSize);
                snappedElement.attributes.y1 = SnapToGrid.snapValue(snappedElement.attributes.y1, gridSize);
                snappedElement.attributes.x2 = SnapToGrid.snapValue(snappedElement.attributes.x2, gridSize);
                snappedElement.attributes.y2 = SnapToGrid.snapValue(snappedElement.attributes.y2, gridSize);
                break;
            case 'text':
                snappedElement.attributes.x = SnapToGrid.snapValue(snappedElement.attributes.x, gridSize);
                snappedElement.attributes.y = SnapToGrid.snapValue(snappedElement.attributes.y, gridSize);
                break;
            // Path snapping is more complex and usually involves snapping individual points in 'd'
        }
        return snappedElement;
    }
}

/**
 * Calculates the bounding box for an SVG element.
 * @param {object} element - The SVG element object.
 * @returns {{x: number, y: number, width: number, height: number} | null} The bounding box, or null if unsupported.
 */
export function getElementBounds(element, includeRotation = true) {
    const attrs = element.attributes;
    let x, y, width, height, cx, cy;

    const transform = attrs.transform || '';
    const translateMatch = transform.match(/translate\(([^,]+),([^)]+)\)/);
    const tx = translateMatch ? parseFloat(translateMatch[1]) : 0;
    const ty = translateMatch ? parseFloat(translateMatch[2]) : 0;


    switch (element.type) {
        case 'rect':
            x = parseFloat(attrs.x);
            y = parseFloat(attrs.y);
            width = parseFloat(attrs.width);
            height = parseFloat(attrs.height);
            break;
        case 'circle':
            x = parseFloat(attrs.cx) - parseFloat(attrs.r);
            y = parseFloat(attrs.cy) - parseFloat(attrs.r);
            width = parseFloat(attrs.r) * 2;
            height = parseFloat(attrs.r) * 2;
            break;
        case 'ellipse':
            x = parseFloat(attrs.cx) - parseFloat(attrs.rx);
            y = parseFloat(attrs.cy) - parseFloat(attrs.ry);
            width = parseFloat(attrs.rx) * 2;
            height = parseFloat(attrs.ry) * 2;
            break;
        case 'line':
            // For lines, the bounding box is min/max of x1,x2 and y1,y2
            x = Math.min(parseFloat(attrs.x1), parseFloat(attrs.x2));
            y = Math.min(parseFloat(attrs.y1), parseFloat(attrs.y2));
            width = Math.abs(parseFloat(attrs.x2) - parseFloat(attrs.x1));
            height = Math.abs(parseFloat(attrs.y2) - parseFloat(attrs.y1));
            break;
        case 'text':
            // Text bounding box is more complex due to font metrics.
            // This is an approximation. For accurate bounds, you'd need to render it
            // and use getBBox() or a text measurement library.
            // Assuming default text alignment and a rough width/height.
            const fontSize = parseFloat(attrs['font-size'] || 16);
            const textContent = element.textContent || 'Text';
            // Rough estimate: 0.6 * font size per character
            x = parseFloat(attrs.x);
            y = parseFloat(attrs.y) - fontSize; // Adjust y to top of text box
            width = textContent.length * (fontSize * 0.6);
            height = fontSize * 1.2; // A bit more than font size for line height
            break;
        case 'path':
             // This is a simplified approach for paths. A proper implementation
            // would parse the 'd' attribute to find the exact bounding box.
            const points = (attrs.d || '').split(/[ML]/).filter(p => p).map(p => {
                const [px, py] = p.trim().split(/[, ]/);
                return { x: parseFloat(px), y: parseFloat(py) };
            });
            if (points.length === 0) return null;
            const minX = Math.min(...points.map(p => p.x));
            const minY = Math.min(...points.map(p => p.y));
            const maxX = Math.max(...points.map(p => p.x));
            const maxY = Math.max(...points.map(p => p.y));
            x = minX;
            y = minY;
            width = maxX - minX;
            height = maxY - minY;
            break;
        default:
            return null;
    }

    cx = x + width / 2;
    cy = y + height / 2;

    const rotatedBounds = { x: x + tx, y: y + ty, width, height, cx: cx + tx, cy: cy + ty, rotation: attrs.rotation || 0 };

    if (includeRotation && attrs.rotation) {
        const angle = attrs.rotation * Math.PI / 180;
        const corners = [
            { x: rotatedBounds.x, y: rotatedBounds.y },
            { x: rotatedBounds.x + width, y: rotatedBounds.y },
            { x: rotatedBounds.x, y: rotatedBounds.y + height },
            { x: rotatedBounds.x + width, y: rotatedBounds.y + height },
        ];
        const rotatedCorners = corners.map(p => {
            const dx = p.x - rotatedBounds.cx;
            const dy = p.y - rotatedBounds.cy;
            return {
                x: rotatedBounds.cx + dx * Math.cos(angle) - dy * Math.sin(angle),
                y: rotatedBounds.cy + dx * Math.sin(angle) + dy * Math.cos(angle),
            };
        });
        const minX = Math.min(...rotatedCorners.map(p => p.x));
        const minY = Math.min(...rotatedCorners.map(p => p.y));
        const maxX = Math.max(...rotatedCorners.map(p => p.x));
        const maxY = Math.max(...rotatedCorners.map(p => p.y));
        return { x: minX, y: minY, width: maxX - minX, height: maxY - minY, cx: rotatedBounds.cx, cy: rotatedBounds.cy, rotation: attrs.rotation };
    }


    return rotatedBounds;
}

/**
 * Generates an array of resize handle coordinates for a given bounding box.
 * @param {{x: number, y: number, width: number, height: number}} bounds - The bounding box of the element.
 * @returns {Array<{name: string, x: number, y: number}>} Array of handle objects.
 */
export function getResizeHandles(bounds) {
    if (!bounds) return [];
    const { x, y, width, height, cx, cy, rotation } = bounds;
    const angle = (rotation || 0) * Math.PI / 180;

    const points = [
        { name: 'nw', x: x, y: y },
        { name: 'ne', x: x + width, y: y },
        { name: 'sw', x: x, y: y + height },
        { name: 'se', x: x + width, y: y + height },
        { name: 'n', x: x + width / 2, y: y },
        { name: 's', x: x + width / 2, y: y + height },
        { name: 'w', x: x, y: y + height / 2 },
        { name: 'e', x: x + width, y: y + height / 2 },
        { name: 'rotate', x: cx, y: y - 30 },
    ];
    if (rotation) {
        return points.map(p => {
            const dx = p.x - cx;
            const dy = p.y - cy;
            return {
                name: p.name,
                x: cx + dx * Math.cos(angle) - dy * Math.sin(angle),
                y: cy + dx * Math.sin(angle) + dy * Math.cos(angle),
            };
        });
    }

    return points;
}