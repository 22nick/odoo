/** @odoo-module **/

import { Component, useState, useRef, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

class VectorEditorField extends Component {
    setup() {
        this.canvasRef = useRef("canvas");
        this.state = useState({
            shapes: [],
            selectedShape: null,
            isDragging: false,
            isResizing: false,
            isRotating: false,
            dragStart: { x: 0, y: 0 },
            resizeHandle: null,
            tool: 'select' // 'select' or 'rectangle'
        });

        onMounted(() => {
            this.loadData();
            this.setupCanvas();
        });
    }

    loadData() {
        try {
            const data = this.props.value ? JSON.parse(this.props.value) : { shapes: [] };
            this.state.shapes = data.shapes || [];
        } catch (e) {
            this.state.shapes = [];
        }
    }

    setupCanvas() {
        const canvas = this.canvasRef.el;
        canvas.addEventListener('mousedown', this.onMouseDown.bind(this));
        canvas.addEventListener('mousemove', this.onMouseMove.bind(this));
        canvas.addEventListener('mouseup', this.onMouseUp.bind(this));
        canvas.addEventListener('dblclick', this.onDoubleClick.bind(this));
        this.render();
    }

    getMousePos(e) {
        const canvas = this.canvasRef.el;
        const rect = canvas.getBoundingClientRect();
        return {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
    }

    onMouseDown(e) {
        const pos = this.getMousePos(e);

        if (this.state.tool === 'rectangle') {
            // Create new rectangle
            const newShape = {
                id: Date.now(),
                type: 'rectangle',
                x: pos.x,
                y: pos.y,
                width: 100,
                height: 60,
                rotation: 0,
                text: 'Текст',
                fillColor: '#3498db',
                textColor: '#ffffff'
            };
            this.state.shapes.push(newShape);
            this.state.selectedShape = newShape;
            this.saveData();
            this.render();
            return;
        }

        // Check if clicked on resize handle
        if (this.state.selectedShape) {
            const handle = this.getResizeHandle(pos, this.state.selectedShape);
            if (handle) {
                this.state.isResizing = true;
                this.state.resizeHandle = handle;
                this.state.dragStart = { ...pos };
                return;
            }

            // Check rotation handle
            if (this.isOnRotationHandle(pos, this.state.selectedShape)) {
                this.state.isRotating = true;
                this.state.dragStart = { ...pos };
                return;
            }
        }

        // Check if clicked on a shape
        const clickedShape = this.findShapeAt(pos);
        if (clickedShape) {
            this.state.selectedShape = clickedShape;
            this.state.isDragging = true;
            this.state.dragStart = {
                x: pos.x - clickedShape.x,
                y: pos.y - clickedShape.y
            };
        } else {
            this.state.selectedShape = null;
        }
        this.render();
    }

    onMouseMove(e) {
        const pos = this.getMousePos(e);

        if (this.state.isDragging && this.state.selectedShape) {
            this.state.selectedShape.x = pos.x - this.state.dragStart.x;
            this.state.selectedShape.y = pos.y - this.state.dragStart.y;
            this.render();
        } else if (this.state.isResizing && this.state.selectedShape) {
            const shape = this.state.selectedShape;
            const dx = pos.x - this.state.dragStart.x;
            const dy = pos.y - this.state.dragStart.y;

            switch (this.state.resizeHandle) {
                case 'se':
                    shape.width = Math.max(30, shape.width + dx);
                    shape.height = Math.max(20, shape.height + dy);
                    break;
                case 'sw':
                    const newWidth = Math.max(30, shape.width - dx);
                    shape.x += shape.width - newWidth;
                    shape.width = newWidth;
                    shape.height = Math.max(20, shape.height + dy);
                    break;
                case 'ne':
                    shape.width = Math.max(30, shape.width + dx);
                    const newHeight = Math.max(20, shape.height - dy);
                    shape.y += shape.height - newHeight;
                    shape.height = newHeight;
                    break;
                case 'nw':
                    const nwWidth = Math.max(30, shape.width - dx);
                    const nwHeight = Math.max(20, shape.height - dy);
                    shape.x += shape.width - nwWidth;
                    shape.y += shape.height - nwHeight;
                    shape.width = nwWidth;
                    shape.height = nwHeight;
                    break;
            }

            this.state.dragStart = { ...pos };
            this.render();
        } else if (this.state.isRotating && this.state.selectedShape) {
            const shape = this.state.selectedShape;
            const centerX = shape.x + shape.width / 2;
            const centerY = shape.y + shape.height / 2;
            const angle = Math.atan2(pos.y - centerY, pos.x - centerX);
            shape.rotation = angle * 180 / Math.PI;
            this.render();
        }
    }

    onMouseUp(e) {
        if (this.state.isDragging || this.state.isResizing || this.state.isRotating) {
            this.saveData();
        }
        this.state.isDragging = false;
        this.state.isResizing = false;
        this.state.isRotating = false;
        this.state.resizeHandle = null;
    }

    onDoubleClick(e) {
        const pos = this.getMousePos(e);
        const shape = this.findShapeAt(pos);
        
        if (shape) {
            const newText = prompt('Введите текст:', shape.text);
            if (newText !== null) {
                shape.text = newText;
                this.saveData();
                this.render();
            }
        }
    }

    findShapeAt(pos) {
        for (let i = this.state.shapes.length - 1; i >= 0; i--) {
            const shape = this.state.shapes[i];
            const centerX = shape.x + shape.width / 2;
            const centerY = shape.y + shape.height / 2;
            
            // Transform point to shape's local coordinates
            const angle = -shape.rotation * Math.PI / 180;
            const localX = Math.cos(angle) * (pos.x - centerX) - Math.sin(angle) * (pos.y - centerY) + centerX;
            const localY = Math.sin(angle) * (pos.x - centerX) + Math.cos(angle) * (pos.y - centerY) + centerY;
            
            if (localX >= shape.x && localX <= shape.x + shape.width &&
                localY >= shape.y && localY <= shape.y + shape.height) {
                return shape;
            }
        }
        return null;
    }

    getResizeHandle(pos, shape) {
        const handles = this.getResizeHandles(shape);
        const tolerance = 8;

        for (const [name, handle] of Object.entries(handles)) {
            const dx = pos.x - handle.x;
            const dy = pos.y - handle.y;
            if (Math.sqrt(dx * dx + dy * dy) < tolerance) {
                return name;
            }
        }
        return null;
    }

    getResizeHandles(shape) {
        const centerX = shape.x + shape.width / 2;
        const centerY = shape.y + shape.height / 2;
        const angle = shape.rotation * Math.PI / 180;

        const corners = {
            nw: { x: shape.x, y: shape.y },
            ne: { x: shape.x + shape.width, y: shape.y },
            sw: { x: shape.x, y: shape.y + shape.height },
            se: { x: shape.x + shape.width, y: shape.y + shape.height }
        };

        // Rotate corners around center
        const rotated = {};
        for (const [name, corner] of Object.entries(corners)) {
            const dx = corner.x - centerX;
            const dy = corner.y - centerY;
            rotated[name] = {
                x: centerX + dx * Math.cos(angle) - dy * Math.sin(angle),
                y: centerY + dx * Math.sin(angle) + dy * Math.cos(angle)
            };
        }

        return rotated;
    }

    isOnRotationHandle(pos, shape) {
        const centerX = shape.x + shape.width / 2;
        const centerY = shape.y + shape.height / 2;
        const angle = shape.rotation * Math.PI / 180;
        
        const handleDist = shape.height / 2 + 25;
        const handleX = centerX + handleDist * Math.sin(angle);
        const handleY = centerY - handleDist * Math.cos(angle);
        
        const dx = pos.x - handleX;
        const dy = pos.y - handleY;
        return Math.sqrt(dx * dx + dy * dy) < 8;
    }

    render() {
        const canvas = this.canvasRef.el;
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Draw background
        ctx.fillStyle = '#f5f5f5';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Draw grid
        ctx.strokeStyle = '#e0e0e0';
        ctx.lineWidth = 1;
        for (let x = 0; x < canvas.width; x += 20) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, canvas.height);
            ctx.stroke();
        }
        for (let y = 0; y < canvas.height; y += 20) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(canvas.width, y);
            ctx.stroke();
        }

        // Draw shapes
        this.state.shapes.forEach(shape => {
            this.drawShape(ctx, shape);
        });

        // Draw selection
        if (this.state.selectedShape) {
            this.drawSelection(ctx, this.state.selectedShape);
        }
    }

    drawShape(ctx, shape) {
        ctx.save();
        
        const centerX = shape.x + shape.width / 2;
        const centerY = shape.y + shape.height / 2;
        
        ctx.translate(centerX, centerY);
        ctx.rotate(shape.rotation * Math.PI / 180);
        ctx.translate(-centerX, -centerY);
        
        // Draw rectangle
        ctx.fillStyle = shape.fillColor;
        ctx.fillRect(shape.x, shape.y, shape.width, shape.height);
        
        ctx.strokeStyle = '#2c3e50';
        ctx.lineWidth = 2;
        ctx.strokeRect(shape.x, shape.y, shape.width, shape.height);
        
        // Draw text
        ctx.fillStyle = shape.textColor;
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(shape.text, centerX, centerY);
        
        ctx.restore();
    }

    drawSelection(ctx, shape) {
        const handles = this.getResizeHandles(shape);
        
        // Draw selection outline
        ctx.save();
        ctx.setLineDash([5, 5]);
        ctx.strokeStyle = '#2196F3';
        ctx.lineWidth = 2;
        
        ctx.beginPath();
        ctx.moveTo(handles.nw.x, handles.nw.y);
        ctx.lineTo(handles.ne.x, handles.ne.y);
        ctx.lineTo(handles.se.x, handles.se.y);
        ctx.lineTo(handles.sw.x, handles.sw.y);
        ctx.closePath();
        ctx.stroke();
        ctx.restore();
        
        // Draw resize handles
        ctx.fillStyle = '#2196F3';
        for (const handle of Object.values(handles)) {
            ctx.fillRect(handle.x - 4, handle.y - 4, 8, 8);
        }
        
        // Draw rotation handle
        const centerX = shape.x + shape.width / 2;
        const centerY = shape.y + shape.height / 2;
        const angle = shape.rotation * Math.PI / 180;
        const handleDist = shape.height / 2 + 25;
        const handleX = centerX + handleDist * Math.sin(angle);
        const handleY = centerY - handleDist * Math.cos(angle);
        
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(handleX, handleY);
        ctx.stroke();
        
        ctx.beginPath();
        ctx.arc(handleX, handleY, 6, 0, 2 * Math.PI);
        ctx.fillStyle = '#4CAF50';
        ctx.fill();
    }

    saveData() {
        const data = JSON.stringify({ shapes: this.state.shapes });
        this.props.update(data);
    }

    addRectangle() {
        this.state.tool = 'rectangle';
    }

    selectTool() {
        this.state.tool = 'select';
    }

    deleteSelected() {
        if (this.state.selectedShape) {
            const index = this.state.shapes.indexOf(this.state.selectedShape);
            if (index > -1) {
                this.state.shapes.splice(index, 1);
                this.state.selectedShape = null;
                this.saveData();
                this.render();
            }
        }
    }

    changeColor(color) {
        if (this.state.selectedShape) {
            this.state.selectedShape.fillColor = color;
            this.saveData();
            this.render();
        }
    }
}

VectorEditorField.template = "vector_editor.VectorEditorField";
VectorEditorField.props = {
    ...standardFieldProps,
};

registry.category("fields").add("vector_editor", VectorEditorField);