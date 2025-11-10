import { Component, useState } from "@odoo/owl";

export class Counter extends Component {
    static template = "my_module.Counter";

    setup() {
        this.state = useState({ value: 0 });
    }

    increment() {
        this.state.value++;
    }
}

// odoo.define('student_inherit_views.forging_fields_validate', function (require) {

//     "use strict";

//     console.log("Custom JavaScript In Student Inherit Views");

// });