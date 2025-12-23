/** @odoo-module **/

import { Component, onMounted, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class LayoutEditor extends Component {
    static template = "manufacturing_extension.LayoutEditor";

    setup() {
        this.canvasRef = useRef("canvas");
        this.canvas = null;

        onMounted(() => {
            this.canvas = new fabric.Canvas(this.canvasRef.el, {
                selection: true,
                preserveObjectStacking: true,
            });

            // delete по клавише Del
            window.addEventListener("keydown", (e) => {
                if (e.key === "Delete") {
                    this.removeSelected();
                }
            });

            if (this.props.value?.objects) {
                this.canvas.loadFromJSON(
                    this.props.value,
                    this.canvas.renderAll.bind(this.canvas)
                );
            }

            // Сохранение при изменениях
            this.canvas.on("object:added", () => this.save());
            this.canvas.on("object:modified", () => this.save());
            this.canvas.on("object:removed", () => this.save());


            // Редактирование текста по двойному клику

            this.canvas.on("mouse:dblclick", (e) => {
                const obj = e.target;
                if (obj && obj.type === "group") {
                    const text = obj.item(1);
                    const newLabel = prompt("Label:", text.text);
                    if (newLabel !== null) {
                        text.text = newLabel;
                        obj.custom_label = newLabel;
                        this.canvas.renderAll();
                        this.save();
                    }
                }
            });

            

        });
    }

    addBox() {
        if (!this.canvas) return;

        const rect = new fabric.Rect({
            width: 120,
            height: 60,
            fill: "#e7f1ff",
            stroke: "#2b579a",
            strokeWidth: 1,
            rx: 4,
            ry: 4,
        });

        const text = new fabric.Text("A1", {
            fontSize: 16,
            fill: "#000",
            originX: "center",
            originY: "center",
        });

        const group = new fabric.Group([rect, text], {
            left: 100,
            top: 100,
            lockUniScaling: false,
            hasRotatingPoint: true,
            cornerStyle: "circle",
            transparentCorners: false,
        });

        group.on("scaling", () => {
            const text = group.item(1);
            text.set({
                left: group.width / 2,
                top: group.height / 2,
            });
        });

        group.custom_type = "box";
        group.custom_label = "A1";

        this.canvas.add(group);
        this.canvas.setActiveObject(group);
        this.canvas.renderAll();
        this.save();
    }

    removeSelected() {
        if (!this.canvas) return;

        const active = this.canvas.getActiveObject();
        if (!active) return;

        this.canvas.remove(active);
        this.canvas.discardActiveObject();
        this.canvas.renderAll();
        this.save();
    }

    save() {
        if (typeof this.props.update !== "function") {
            console.warn("Field API not available");
            return;
        }
        const json = this.canvas.toJSON(["custom_type", "custom_label"]);
        this.props.update(json);
    }

    saveManual() {
        if (this.props.readonly) {
            alert("Поле доступно только для просмотра");
            return;
        }

        if (!this.canvas) {
            alert("Canvas ещё не инициализирован");
            return;
        }

        if (typeof this.props.update !== "function") {
            alert("Ошибка сохранения (update недоступен)");
            return;
        }

        const json = this.canvas.toJSON(["custom_type", "custom_label"]);
        this.props.update(json);

        // визуальный фидбек
        this.showSavedFeedback();
    }
    

    showSavedFeedback() {
        const btn = this.el.querySelector(".btn-primary");
        if (!btn) return;

        const original = btn.textContent;
        btn.textContent = "✅ Сохранено";

        setTimeout(() => {
            btn.textContent = original;
        }, 1200);
    }


}

registry.category("fields").add("layout_editor", {
    component: LayoutEditor,
    supportedTypes: ["json"],
});

