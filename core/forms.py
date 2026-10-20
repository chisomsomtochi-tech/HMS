from django import forms

INPUT_CLASS = (
    "block w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm "
    "text-slate-900 placeholder:text-slate-400 shadow-sm transition "
    "focus:border-brand-500 focus:outline-none focus:ring-4 focus:ring-brand-500/10"
)
SELECT_CLASS = INPUT_CLASS + " pr-9"
TEXTAREA_CLASS = INPUT_CLASS + " min-h-24 resize-y"
CHECKBOX_CLASS = (
    "mt-0.5 h-4 w-4 rounded border-slate-300 text-brand-600 "
    "focus:ring-2 focus:ring-brand-500 focus:ring-offset-2"
)
FILE_CLASS = (
    "block w-full text-sm text-slate-600 file:mr-3 file:rounded-lg file:border-0 "
    "file:bg-slate-100 file:px-3 file:py-2 file:text-sm file:font-medium "
    "file:text-slate-700 hover:file:bg-slate-200"
)


class TailwindFormMixin:
    """Applies the shared input styling to every widget on the form."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget

            if isinstance(widget, forms.CheckboxInput):
                css = CHECKBOX_CLASS
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                css = SELECT_CLASS
            elif isinstance(widget, forms.Textarea):
                css = TEXTAREA_CLASS
            elif isinstance(widget, forms.FileInput):
                css = FILE_CLASS
            else:
                css = INPUT_CLASS

            existing = widget.attrs.get("class", "")
            if css not in existing:
                widget.attrs["class"] = f"{existing} {css}".strip()
