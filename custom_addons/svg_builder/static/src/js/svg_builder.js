/** @odoo-module **/
import { Component, useState, useRef, onMounted, onWillUnmount, useExternalListener, onPatched } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { debounce } from "@web/core/utils/timing";
import {
    SvgElementFactory,
    SvgExporter,
    SvgImporter,
    HistoryManager,
    SnapToGrid,
    getToolIcon,
    getElementBounds,
    getResizeHandles
} from "./svg_components";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

// // SVG Preview Field Component (TS)
// import { Component, onMounted } from "@odoo/owl";

// export class SvgPreviewField extends Component {
//     onMounted() {
//         this.el.innerHTML = this.props.value || "";
//     }
// }


export class SvgBuilderComponent extends Component {


    setup() {
        super.setup();
        this.orm = useService("orm");
        this.notification = useService("notification");

        // Refs for DOM elements
        this.svgRef = useRef("svg");
        this.toolbarRef = useRef("toolbar");
        this.propertiesPanelRef = useRef("propertiesPanel");
        this.fileInputRef = useRef("fileInput");
        this.textInputRef = useRef("textInput"); // Ref for the foreignObject textarea

        // Reactive state for the component
        this.state = useState({
            currentTool: 'select', // Current active drawing tool
            selectedElement: null, // The currently selected SVG element (DOM element)
            selectedElementId: null, // The ID of the currently selected element
            selectedElementAttributes: {}, // Attributes of the selected element for properties panel
            selectedElementBounds: null, // Bounding box and handles for selected element

            svgElements: [], // Array of SVG element objects {id, type, attributes, textContent}
            isDrawing: false, // Flag if drawing is in progress
            isMoving: false, // Flag if moving an element is in progress
            isResizing: false, // Flag if resizing an element is in progress
            isRotating: false, // Flag for rotation
            resizeHandle: null, // Which handle is being used for resizing (e.g., 'nw', 'se')
            lShapePoints: [], // Points for drawing an L-shape

            startPoint: { x: 0, y: 0 }, // Start point of drawing/moving/resizing (SVG coordinates)
            lastMousePos: { x: 0, y: 0 }, // Last mouse position for moving/panning (SVG coordinates)

            canvasWidth: 800,
            canvasHeight: 600,
            backgroundColor: '#ffffff',
            zoom: 1, // Canvas zoom level
            panX: 0, // Canvas pan X offset
            panY: 0, // Canvas pan Y offset

            gridSize: 20, // Size of the grid cells
            showGrid: true, // Toggle grid visibility
            snapToGrid: false, // Toggle snap-to-grid functionality
            shiftKey: false, // State of the Shift key for constrained drawing

            editingTextElementId: null, // ID of the text element being edited
            editingTextContent: '', // Content of the text editor
            editingTextPosition: { x: 0, y: 0 }, // Position of the text editor
        });

        // Non-reactive properties
        this.recordId = this.env.model.config.resId ; // Odoo record ID
        this.tools = ['select', 'rectangle', 'circle', 'ellipse', 'line', 'text', 'path', 'lshape'];
        this.historyManager = new HistoryManager();
        this.saveSvgDataDebounced = debounce(this.saveSvgData, 500); // Debounce saving to Odoo

        // Expose helper function to template
        this.getToolIcon = getToolIcon;

        // Lifecycle hooks
        onMounted(() => {
            this.setupEventListeners();
            this.loadSvgData();
            this.addInitialHistoryState();
        });

        onWillUnmount(() => {
            this.removeEventListeners();
        });

        // Focus text input after it's rendered
        onPatched(() => {
            if (this.state.editingTextElementId && this.textInputRef.el) {
                this.textInputRef.el.focus();
                this.textInputRef.el.select(); // Select all text for easy replacement
            }
        });

        // Global listeners for keyboard events
        useExternalListener(document, 'keydown', this.onKeyDown);
        useExternalListener(document, 'keyup', this.onKeyUp);
    }

    /**
     * Sets up event listeners for SVG interactions.
     * These are handled by Owl's useExternalListener for document-level,
     * and directly in template for SVG-specific events.
     */
    setupEventListeners() {
        // SVG events are handled directly in the QWeb template using t-on- directives.
        // This method is mainly for document-level listeners not handled by useExternalListener.
    }

    /**
     * Removes event listeners.
     * useExternalListener handles cleanup automatically for document listeners.
     * SVG events are bound directly in template and managed by Owl.
     */
    removeEventListeners() {
        // No manual cleanup needed here due to Owl's event handling.
    }

    // Add these new methods to the class
    /**
     * Zooms in by a fixed factor, centered on the viewport.
     */
    zoomIn() {
        this.applyZoom(1.2); // Zoom in by 20%
    }

    /**
     * Zooms out by a fixed factor, centered on the viewport.
     */
    zoomOut() {
        this.applyZoom(1 / 1.2); // Zoom out by 20%
    }

    /**
     * Applies a zoom factor, keeping the center of the viewport stable.
     * @param {number} scaleFactor The factor by which to multiply the current zoom.
     */
    applyZoom(scaleFactor) {
        const svgWrapper = this.svgRef.el.parentElement;
        const rect = svgWrapper.getBoundingClientRect();
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;

        this.onWheel({
            preventDefault: () => {},
            deltaY: scaleFactor > 1 ? -1 : 1, // Simulate wheel scroll down/up
            clientX: rect.left + centerX,
            clientY: rect.top + centerY,
        });
    }

    /**
     * Adjusts zoom and pan to fit the entire canvas within the viewport.
     */
    zoomToFit() {
        const svgWrapper = this.svgRef.el.parentElement;
        if (!svgWrapper) return;

        const viewportWidth = svgWrapper.clientWidth;
        const viewportHeight = svgWrapper.clientHeight;
        const canvasWidth = this.state.canvasWidth;
        const canvasHeight = this.state.canvasHeight;

        const scaleX = viewportWidth / canvasWidth;
        const scaleY = viewportHeight / canvasHeight;

        // Use the smaller scale factor to fit the whole canvas, with 5% padding
        const newZoom = Math.min(scaleX, scaleY) * 0.95;

        // Center the canvas
        const newPanX = (viewportWidth - (canvasWidth * newZoom)) / 2 / newZoom;
        const newPanY = (viewportHeight - (canvasHeight * newZoom)) / 2 / newZoom;

        this.state.zoom = newZoom;
        this.state.panX = newPanX;
        this.state.panY = newPanY;
    }

    /**
     * Converts screen coordinates to SVG coordinates, accounting for zoom and pan.
     * @param {number} clientX - Mouse event clientX.
     * @param {number} clientY - Mouse event clientY.
     * @returns {{x: number, y: number}} SVG coordinates.
     */
    getSvgCoordinates(clientX, clientY) {
        const svg = this.svgRef.el;
        if (!svg) return { x: 0, y: 0 };

        const rect = svg.getBoundingClientRect();
        let x = (clientX - rect.left) / this.state.zoom - this.state.panX;
        let y = (clientY - rect.top) / this.state.zoom - this.state.panY;

        if (this.state.snapToGrid) {
            x = SnapToGrid.snapValue(x, this.state.gridSize);
            y = SnapToGrid.snapValue(y, this.state.gridSize);
        }
        return { x, y };
    }

    /**
     * Loads SVG data from the Odoo backend for the current record.
     */
    async loadSvgData() {
        // Get the record ID from the parent container's data attribute
        const container = this.svgRef.el?.closest('.svg-builder-container');
        this.recordId = this.env.model.config.resId;

        if (this.recordId) {
            try {
                const record = await this.orm.read("svg.builder", [parseInt(this.recordId)],
                    ["svg_content", "width", "height", "background_color"]);

                if (record.length > 0) {
                    const data = record[0];
                    this.state.canvasWidth = data.width || 800;
                    this.state.canvasHeight = data.height || 600;
                    this.state.backgroundColor = data.background_color || '#ffffff';

                    if (data.svg_content) {
                        // Parse the SVG content and update svgElements state
                        const parsedElements = SvgImporter.parseSvgContent(data.svg_content);
                        this.state.svgElements = parsedElements;
                    }
                    this.addInitialHistoryState(); // Add loaded state to history
                }
            } catch (error) {
                console.error('Error loading SVG data:', error);
                this.notification.add('Error loading SVG data. Check console for details.', { type: 'danger' });
            }
        }
    }

    /**
     * Handles double click on the SVG to finish path-like drawings.
     * @param {MouseEvent} event
     */
    onSvgDoubleClick(event) {
        if (this.state.isDrawing && this.state.currentTool === 'lshape') {
            // Remove the last point, which was added on the second click of the dblclick
            this.state.lShapePoints.pop();
            this.finishDrawing();
        }
    }

    /**
     * Handles mouse down event on the SVG canvas.
     * Initiates drawing, moving, or resizing.
     * @param {MouseEvent} event
     */
    onSvgMouseDown(event) {
        // Prevent default browser drag behavior
        event.preventDefault();

        // If editing text, finish editing first
        if (this.state.editingTextElementId) {
            this.finishTextEdit();
            return;
        }

        const svgCoords = this.getSvgCoordinates(event.clientX, event.clientY);
        this.state.startPoint = svgCoords;
        this.state.lastMousePos = svgCoords; // Initialize last mouse position for pan/move

        const target = event.target;
        const handleElement = target.closest('[data-handle]');
        const elementId = target.closest('[data-element-id]')?.getAttribute('data-element-id');
        const handleName = handleElement ? handleElement.getAttribute('data-handle') : null;


        if (handleName) {
            // Start resizing or rotating
            if (handleName === 'rotate') {
                this.state.isRotating = true;
            } else {
                this.state.isResizing = true;
                this.state.resizeHandle = handleName;
            }
            this.state.selectedElement = this.state.svgElements.find(el => el.id === elementId);
            this.state.selectedElementId = elementId;
            this.updateSelectedElementAttributes();
            this.updateSelectedElementBounds();

        } else if (elementId && this.state.currentTool === 'select') {
            // Start moving an existing element
            this.state.isMoving = true;
            this.state.selectedElement = this.state.svgElements.find(el => el.id === elementId);
            this.state.selectedElementId = elementId;
            this.updateSelectedElementAttributes();
            this.updateSelectedElementBounds();
        } else if (target.tagName === 'svg' && this.state.currentTool === 'select') {
            // Clicked on empty canvas with select tool, deselect
            this.state.selectedElement = null;
            this.state.selectedElementId = null;
            this.state.selectedElementAttributes = {};
            this.state.selectedElementBounds = null;
        } else if (this.state.currentTool !== 'select') {
             if (this.state.currentTool === 'lshape') {
                if (!this.state.isDrawing) {
                    // First click: start drawing
                    this.state.isDrawing = true;
                    this.state.lShapePoints.push(svgCoords);
                    const newElement = SvgElementFactory.createElement('path', svgCoords);
                    this.state.svgElements.push(newElement);
                    this.state.selectedElement = newElement;
                } else {
                    // Subsequent clicks: add a new constrained point
                    const lastPoint = this.state.lShapePoints[this.state.lShapePoints.length - 1];
                    let nextPoint;

                    // Constrain the new point to be horizontal or vertical
                    if (this.state.lShapePoints.length % 2 !== 0) { // Next segment is horizontal
                        nextPoint = { x: svgCoords.x, y: lastPoint.y };
                    } else { // Next segment is vertical
                        nextPoint = { x: lastPoint.x, y: svgCoords.y };
                    }

                    this.state.lShapePoints.push(nextPoint);
                    // Update the element with the new fixed point
                    SvgElementFactory.updateLShape(this.state.selectedElement, this.state.lShapePoints, svgCoords);
                }
            } else {
                this.state.isDrawing = true;
                const newElement = SvgElementFactory.createElement(this.state.currentTool, svgCoords);
                if (newElement) {

                    this.state.svgElements.push(newElement);
                    this.state.selectedElement = newElement; // Select the newly drawn element
                    this.state.selectedElementId = newElement.id;
                    this.updateSelectedElementAttributes();
                    this.updateSelectedElementBounds();
                }
            }
        }
    }

    /**
     * Handles mouse move event on the SVG canvas.
     * Updates element dimensions during drawing, moves elements, or resizes elements.
     * @param {MouseEvent} event
     */
    onSvgMouseMove(event) {
        const currentSvgCoords = this.getSvgCoordinates(event.clientX, event.clientY);
        if (this.state.isDrawing && this.state.currentTool === 'lshape' && this.state.selectedElement) {
            SvgElementFactory.updateLShape(this.state.selectedElement, this.state.lShapePoints, currentSvgCoords);
            return;
        }


        if (!this.state.isDrawing && !this.state.isMoving && !this.state.isResizing && !this.state.isRotating) return;


        const dx = currentSvgCoords.x - this.state.lastMousePos.x;
        const dy = currentSvgCoords.y - this.state.lastMousePos.y;

        if (this.state.isDrawing) {
            const lastElement = this.state.svgElements[this.state.svgElements.length - 1];
            if (lastElement) {
                SvgElementFactory.updateElement(lastElement, this.state.startPoint, currentSvgCoords, this.state.shiftKey);
            }
        } else if (this.state.isMoving && this.state.selectedElement) {
            SvgElementFactory.moveElement(this.state.selectedElement, dx, dy);
        } else if (this.state.isResizing && this.state.selectedElement) {
            SvgElementFactory.resizeElement(this.state.selectedElement, this.state.resizeHandle, this.state.startPoint, currentSvgCoords, this.state.shiftKey);
        } else if (this.state.isRotating && this.state.selectedElement) {
            SvgElementFactory.rotateElement(this.state.selectedElement, currentSvgCoords);
        }

        this.state.lastMousePos = currentSvgCoords;
        // Update selected element bounds dynamically during move/resize
        if (this.state.selectedElement) {
            this.updateSelectedElementBounds();
        }
    }

    /**
     * Handles mouse up event on the SVG canvas.
     * Finalizes drawing, moving, or resizing.
     * @param {MouseEvent} event
     */
    onSvgMouseUp(event) {
         if (this.state.currentTool === 'lshape' && this.state.isDrawing) {
            // For the L-shape tool, mouse up doesn't finish the drawing.
            return;
        }

        if (this.state.isDrawing || this.state.isMoving || this.state.isResizing || this.state.isRotating) {
            this.addHistoryState(); // Save state to history after an action
            this.saveSvgDataDebounced(); // Debounced save to Odoo
        }
        this.state.isDrawing = false;
        this.state.isMoving = false;
        this.state.isResizing = false;
        this.state.isRotating = false;
        this.state.resizeHandle = null;
        // Ensure selected element attributes are up-to-date after manipulation
        if (this.state.selectedElement) {
            this.updateSelectedElementAttributes();
            this.updateSelectedElementBounds(); // Recalculate bounds after final position
        }
    }

    /**
     * Finishes the current drawing action, especially for paths.
     */
    finishDrawing() {
       if (this.state.isDrawing && this.state.selectedElement) {
            // Finalize the shape without the mouse-move preview segment
            if (this.state.currentTool === 'lshape') {
                 SvgElementFactory.updateLShape(this.state.selectedElement, this.state.lShapePoints, null);
            }
            this.addHistoryState();
            this.saveSvgDataDebounced();
        }
        this.state.isDrawing = false;
        this.state.lShapePoints = [];
        this.state.selectedElement = null;
        this.state.selectedElementId = null;
    }


    /**
     * Handles mouse down event on a resize handle.
     * @param {MouseEvent} event
     */
    onHandleMouseDown(event) {
        event.stopPropagation(); // Prevent onSvgMouseDown from being triggered
        this.onSvgMouseDown(event); // Reuse the SVG mouse down logic for handles
    }

    /**
     * Handles keyboard key down events for shortcuts.
     * @param {KeyboardEvent} event
     */
    onKeyDown(event) {
        this.state.shiftKey = event.shiftKey;

        // Prevent default browser shortcuts for common actions
        if (event.ctrlKey || event.metaKey) { // Ctrl for Windows/Linux, Cmd for Mac
            switch (event.key) {
                case 'z': // Undo
                    event.preventDefault();
                    if (event.shiftKey) {
                        this.redo();
                    } else {
                        this.undo();
                    }
                    break;
                case 'y': // Redo (alternative)
                    event.preventDefault();
                    this.redo();
                    break;
                case 's': // Save (to Odoo)
                    event.preventDefault();
                    this.saveSvgData();
                    break;
            }
        }

        // Delete key
        if (event.key === 'Delete' || event.key === 'Backspace') {
            if (this.state.editingTextElementId) return; // Don't delete element if editing text
            event.preventDefault();
            this.deleteSelectedElement();
        }

        // Enter key to finish drawing a path
        if (event.key === 'Enter' && this.state.isDrawing && (this.state.currentTool === 'lshape' || this.state.currentTool === 'path')) {
            event.preventDefault();
            this.finishDrawing();
        }

        // Escape key to deselect or cancel text editing
        if (event.key === 'Escape') {
            if (this.state.editingTextElementId) {
                this.finishTextEdit(true); // Cancel text edit
            } else if (this.state.selectedElement) {
                this.state.selectedElement = null;
                this.state.selectedElementId = null;
                this.state.selectedElementAttributes = {};
                this.state.selectedElementBounds = null;
                this.state.currentTool = 'select'; // Revert to select tool
            }
        }
    }

    /**
     * Handles keyboard key up events.
     * @param {KeyboardEvent} event
     */
    onKeyUp(event) {
        this.state.shiftKey = event.shiftKey;
    }

    /**
     * Sets the active drawing tool.
     * @param {string} tool - The name of the tool (e.g., 'rectangle', 'circle', 'select').
     */
    setTool(tool) {
        this.finishDrawing();
        this.state.currentTool = tool;
        this.state.selectedElement = null;
        this.state.selectedElementId = null;
        this.state.selectedElementAttributes = {};
        this.state.selectedElementBounds = null;
        this.state.isDrawing = false;
        this.state.isMoving = false;
        this.state.isResizing = false;
        this.state.isRotating = false;
        this.state.resizeHandle = null;
        // If switching tool while editing text, finish editing
        if (this.state.editingTextElementId) {
            this.finishTextEdit();
        }
    }

    /**
     * Updates the attributes of the currently selected element.
     * This is called from the properties panel.
     * @param {string} property - The attribute name (e.g., 'fill', 'stroke-width').
     * @param {any} value - The new value for the attribute.
     */
    updateElementProperty(property, value) {
        if (this.state.selectedElementId) {
            const elementIndex = this.state.svgElements.findIndex(el => el.id === this.state.selectedElementId);
            if (elementIndex !== -1) {
                // Create a copy to ensure reactivity
                const updatedElements = [...this.state.svgElements];
                const elementToUpdate = { ...updatedElements[elementIndex] };

                if (property === 'textContent') {
                    elementToUpdate.textContent = value;
                } else if (property === 'rotation') {
                    elementToUpdate.attributes = { ...elementToUpdate.attributes, rotation: value };
                    SvgElementFactory.applyRotation(elementToUpdate);
                } else {
                    elementToUpdate.attributes = { ...elementToUpdate.attributes, [property]: value };
                }

                updatedElements[elementIndex] = elementToUpdate;
                this.state.svgElements = updatedElements;
                // Update selected element in state to reflect changes immediately in properties panel
                this.state.selectedElement = elementToUpdate;
                this.updateSelectedElementAttributes(); // Re-fetch updated attributes for panel
                this.updateSelectedElementBounds(); // Re-calculate bounds if position/size attributes changed
                this.addHistoryState(); // Add state to history
                this.saveSvgDataDebounced(); // Debounced save to Odoo
            }
        }
    }

    /**
     * Deletes the currently selected SVG element.
     */
    deleteSelectedElement() {
        if (this.state.selectedElementId) {
            this.state.svgElements = this.state.svgElements.filter(el => el.id !== this.state.selectedElementId);
            this.state.selectedElement = null;
            this.state.selectedElementId = null;
            this.state.selectedElementAttributes = {};
            this.state.selectedElementBounds = null;
            this.addHistoryState(); // Add state to history
            this.saveSvgDataDebounced(); // Debounced save to Odoo
        }
    }

    /**
     * Clears all SVG elements from the canvas.
     */
    clearCanvas() {
        if (confirm('Are you sure you want to clear the entire canvas? This action cannot be undone unless you undo immediately after.')) {
            this.state.svgElements = [];
            this.state.selectedElement = null;
            this.state.selectedElementId = null;
            this.state.selectedElementAttributes = {};
            this.state.selectedElementBounds = null;
            this.historyManager.clear(); // Clear history as well
            this.addInitialHistoryState(); // Add an empty state to history
            this.saveSvgDataDebounced(); // Debounced save to Odoo
        }
    }

    /**
     * Generates the full SVG content string from the current elements and canvas settings.
     * @returns {string} The complete SVG XML string.
     */
    generateSvgContent() {
        return SvgExporter.generateSvgContent(
            this.state.svgElements,
            this.state.canvasWidth,
            this.state.canvasHeight,
            this.state.backgroundColor
        );
    }

    /**
     * Exports the current SVG content as a file (SVG or PNG).
     * @param {'svg' | 'png'} format - The desired export format.
     */
    exportSvg(format) {
        const svgContent = this.generateSvgContent();
        const filename = `drawing_${Date.now()}.${format}`;
        if (format === 'svg') {
            SvgExporter.exportAsFile(svgContent, filename);
        } else if (format === 'png') {
            SvgExporter.exportAsPng(svgContent, this.state.canvasWidth, this.state.canvasHeight, filename);
        }
    }

    /**
     * Imports SVG content from a selected file.
     * @param {Event} event - The file input change event.
     */
    async importSvg(event) {
        const file = event.target.files[0];
        if (file) {
            try {
                const importedElements = await SvgImporter.parseSvgFile(file);
                this.state.svgElements = [...this.state.svgElements, ...importedElements]; // Add to existing elements
                this.state.selectedElement = null;
                this.state.selectedElementId = null;
                this.state.selectedElementAttributes = {};
                this.state.selectedElementBounds = null;
                this.addHistoryState(); // Add state to history
                this.saveSvgDataDebounced(); // Debounced save to Odoo
                this.notification.add('SVG imported successfully!', { type: 'success' });
            } catch (error) {
                console.error('Error importing SVG:', error);
                this.notification.add('Failed to import SVG. Invalid file or content.', { type: 'danger' });
            } finally {
                // Clear the file input value to allow re-importing the same file
                event.target.value = '';
            }
        }
    }

    /**
     * Saves the current SVG content and canvas settings to the Odoo backend.
     */
    async saveSvgData() {
        if (this.recordId) {
            try {
                const svgContent = this.generateSvgContent();
                await this.orm.write("svg.builder", [parseInt(this.recordId)], {
                    svg_content: svgContent,
                    width: this.state.canvasWidth,
                    height: this.state.canvasHeight,
                    background_color: this.state.backgroundColor
                });
                // this.notification.add('SVG saved successfully!', { type: 'success', sticky: false, life: 1000 });
            } catch (error) {
                console.error('Error saving SVG data:', error);
                this.notification.add('Error saving SVG data. Check console for details.', { type: 'danger' });
            }
        }
    }

    /**
     * Adds the current state of svgElements to the history manager.
     */
    addHistoryState() {
        // Only add if there's a significant change (e.g., more than just moving mouse)
        // A simple deep copy of svgElements is sufficient for history
        this.historyManager.addState({
            elements: JSON.parse(JSON.stringify(this.state.svgElements)),
            selectedElementId: this.state.selectedElementId // Preserve selected element in history
        });
    }

    /**
     * Adds the initial state to the history manager.
     * Called on component mount and after loading data.
     */
    addInitialHistoryState() {
        this.historyManager.clear(); // Clear any previous history
        this.historyManager.addState({
            elements: JSON.parse(JSON.stringify(this.state.svgElements)),
            selectedElementId: null
        });
    }

    /**
     * Undoes the last action.
     */
    undo() {
        const prevState = this.historyManager.undo();
        if (prevState) {
            this.state.svgElements = prevState.elements;
            this.state.selectedElementId = prevState.selectedElementId;
            this.state.selectedElement = this.state.svgElements.find(el => el.id === prevState.selectedElementId) || null;
            this.updateSelectedElementAttributes();
            this.updateSelectedElementBounds();
            this.saveSvgDataDebounced();
        } else {
            this.notification.add('Nothing to undo.', { type: 'info', sticky: false, life: 1000 });
        }
    }

    /**
     * Redoes the last undone action.
     */
    redo() {
        const nextState = this.historyManager.redo();
        if (nextState) {
            this.state.svgElements = nextState.elements;
            this.state.selectedElementId = nextState.selectedElementId;
            this.state.selectedElement = this.state.svgElements.find(el => el.id === nextState.selectedElementId) || null;
            this.updateSelectedElementAttributes();
            this.updateSelectedElementBounds();
            this.saveSvgDataDebounced();
        } else {
            this.notification.add('Nothing to redo.', { type: 'info', sticky: false, life: 1000 });
        }
    }

    /**
     * Computes the attributes of the selected element for display in the properties panel.
     * This is a reactive getter.
     */
    updateSelectedElementAttributes() {
        if (this.state.selectedElement) {
            // Merge attributes and textContent for display
            this.state.selectedElementAttributes = {
                ...this.state.selectedElement.attributes,
                type: this.state.selectedElement.type, // Add type for conditional rendering in panel
                textContent: this.state.selectedElement.textContent || '',
                rotation: this.state.selectedElement.attributes.rotation || 0,
            };
        } else {
            this.state.selectedElementAttributes = {};
        }
    }

    /**
     * Computes the bounding box and resize handles for the selected element.
     * This is a reactive getter.
     */
    updateSelectedElementBounds() {
        if (this.state.selectedElement) {
            const bounds = getElementBounds(this.state.selectedElement);
            if (bounds) {
                this.state.selectedElementBounds = {
                    ...bounds,
                    handles: getResizeHandles(bounds)
                };
            } else {
                this.state.selectedElementBounds = null;
            }
        } else {
            this.state.selectedElementBounds = null;
        }
    }

    /**
     * Handles mouse wheel event for zooming.
     * @param {WheelEvent} event
     */
    onWheel(event) {
        event.preventDefault(); // Prevent page scrolling

        const scaleFactor = 1.1; // Zoom in/out by 10%
        let newZoom = this.state.zoom;

        if (event.deltaY < 0) {
            newZoom *= scaleFactor; // Zoom in
        } else {
            newZoom /= scaleFactor; // Zoom out
        }

        // Clamp zoom level
        newZoom = Math.max(0.1, Math.min(5, newZoom));

        // Calculate new pan to zoom around mouse cursor
        const svg = this.svgRef.el;
        if (!svg) return;

        const rect = svg.getBoundingClientRect();
        const mouseX = (event.clientX - rect.left);
        const mouseY = (event.clientY - rect.top);

        const oldSvgX = (mouseX / this.state.zoom) - this.state.panX;
        const oldSvgY = (mouseY / this.state.zoom) - this.state.panY;

        const newPanX = (mouseX / newZoom) - oldSvgX;
        const newPanY = (mouseY / newZoom) - oldSvgY;

        this.state.zoom = newZoom;
        this.state.panX = newPanX;
        this.state.panY = newPanY;
    }

    /**
     * Starts the panning operation.
     * @param {MouseEvent} event
     */
    startPan(event) {
        // Only pan if clicking on empty SVG area with select tool

        if (event.target.tagName === 'svg' && this.state.currentTool === 'select') {
            this.state.isPanning = true;
            this.state.lastMousePos = { x: event.clientX, y: event.clientY };
            this.svgRef.el.style.cursor = 'grabbing'; // Change cursor
        }
    }

    /**
     * Continues the panning operation.
     * @param {MouseEvent} event
     */
    pan(event) {
        if (!this.state.isPanning) return;

        const dx = event.clientX - this.state.lastMousePos.x;
        const dy = event.clientY - this.state.lastMousePos.y;

        this.state.panX += dx / this.state.zoom;
        this.state.panY += dy / this.state.zoom;

        this.state.lastMousePos = { x: event.clientX, y: event.clientY };
    }

    /**
     * Ends the panning operation.
     * @param {MouseEvent} event
     */
    endPan(event) {
        if (this.state.isPanning) {
            this.state.isPanning = false;
            this.svgRef.el.style.cursor = 'grab'; // Reset cursor
        }
    }

    /**
     * Generates an array of line objects for rendering the grid.
     * This is a computed property.
     * @returns {Array<{x1, y1, x2, y2}>}
     */
    getGridLines() {
        const lines = [];
        const gridSize = this.state.gridSize;
        const width = this.state.canvasWidth;
        const height = this.state.canvasHeight;

        // Vertical lines
        for (let x = 0; x <= width; x += gridSize) {
            lines.push({ x1: x, y1: 0, x2: x, y2: height });
        }
        // Horizontal lines
        for (let y = 0; y <= height; y += gridSize) {
            lines.push({ x1: 0, y1: y, x2: width, y2: y });
        }
        return lines;
    }

    /**
     * Starts editing a text element.
     * Shows a foreignObject textarea at the text element's position.
     * @param {string} elementId - The ID of the text element to edit.
     */
    startTextEdit(elementId) {
        const textElement = this.state.svgElements.find(el => el.id === elementId);
        if (textElement && textElement.type === 'text') {
            this.state.editingTextElementId = elementId;
            this.state.editingTextContent = textElement.textContent || '';
            // Position the foreignObject relative to the SVG element's coordinates
            this.state.editingTextPosition = {
                x: parseFloat(textElement.attributes.x),
                y: parseFloat(textElement.attributes.y) - parseFloat(textElement.attributes['font-size'] || 16) // Adjust y for text baseline
            };
            this.state.selectedElement = textElement; // Select the text element when editing
            this.state.selectedElementId = elementId;
            this.updateSelectedElementAttributes();
            this.updateSelectedElementBounds();
        }
    }

    /**
     * Finishes editing a text element.
     * Updates the textContent and hides the textarea.
     * @param {boolean} [cancel=false] - If true, cancels editing without saving changes.
     */
    finishTextEdit(cancel = false) {
        if (!this.state.editingTextElementId) return;

        const textElementIndex = this.state.svgElements.findIndex(el => el.id === this.state.editingTextElementId);
        if (textElementIndex !== -1) {
            const updatedElements = [...this.state.svgElements];
            const elementToUpdate = { ...updatedElements[textElementIndex] };

            if (!cancel) {
                elementToUpdate.textContent = this.state.editingTextContent;
            }
            updatedElements[textElementIndex] = elementToUpdate;
            this.state.svgElements = updatedElements;
            this.addHistoryState();
            this.saveSvgDataDebounced();
        }

        this.state.editingTextElementId = null;
        this.state.editingTextContent = '';
        this.state.editingTextPosition = { x: 0, y: 0 };
    }

    /**
     * Handles keydown events in the text input area.
     * Allows finishing edit with Enter (Ctrl+Enter for newline) and Escape.
     * @param {KeyboardEvent} event
     */
    onTextInputKeyDown(event) {
        if (event.key === 'Enter' && !event.ctrlKey) {
            event.preventDefault(); // Prevent newline in single-line mode
            this.finishTextEdit();
        } else if (event.key === 'Escape') {
            event.preventDefault();
            this.finishTextEdit(true); // Cancel edit
        }
    }
}
SvgBuilderComponent.props = {
    ...standardWidgetProps,
};
SvgBuilderComponent.template = "svg_builder.SvgBuilderTemplate";
export const svgBuilderComponent = {
    component: SvgBuilderComponent,
};

// Register the component as a form widget
registry.category("view_widgets").add("svg_builder", svgBuilderComponent);

// // Register a field type for SVG preview in form views (TS)

// SvgPreviewField.template = "svg_builder.SvgPreviewField";

// // import { SvgPreviewField } from './svg_preview_field.js';

// registry.category("fields").add("svg_preview", {
//     component: SvgPreviewField,
// });