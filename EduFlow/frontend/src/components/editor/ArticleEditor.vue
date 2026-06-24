<script setup lang="ts">
import { ref, reactive, computed, watch, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import { Extension, Node as TiptapNode, getHTMLFromFragment } from '@tiptap/core'
import { Fragment as PmFragment } from 'prosemirror-model'
import Paragraph from '@tiptap/extension-paragraph'
import Heading from '@tiptap/extension-heading'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import TextStyle from '@tiptap/extension-text-style'
import FontFamily from '@tiptap/extension-font-family'
import Color from '@tiptap/extension-color'
import Highlight from '@tiptap/extension-highlight'
import Superscript from '@tiptap/extension-superscript'
import Subscript from '@tiptap/extension-subscript'
import Image from '@tiptap/extension-image'
import Link from '@tiptap/extension-link'
import Placeholder from '@tiptap/extension-placeholder'
import Table from '@tiptap/extension-table'
import TableRow from '@tiptap/extension-table-row'
import TableCell from '@tiptap/extension-table-cell'
import TableHeader from '@tiptap/extension-table-header'
import TextAlign from '@tiptap/extension-text-align'
import TaskList from '@tiptap/extension-task-list'
import TaskItem from '@tiptap/extension-task-item'
import { Markdown } from 'tiptap-markdown'
import katex from 'katex'
import { createArticle, updateArticle, getCategories } from '@/api/article.api'
import { uploadImage } from '@/services/storage.service'
import type { ArticleResponse, ArticleRequest, CategoryEntity } from '@/types/article.types'

const props = defineProps<{
  initialData?: ArticleResponse | null
  articleId?: number | null
}>()

const router = useRouter()

// ── Custom FontSize extension ─────────────────────────────────────────────────
const FontSize = Extension.create({
  name: 'fontSize',
  addOptions: () => ({ types: ['textStyle'] }),
  addGlobalAttributes() {
    return [{
      types: this.options.types,
      attributes: {
        fontSize: {
          default: null,
          parseHTML: (el: Element) => (el as HTMLElement).style.fontSize || null,
          renderHTML: (attrs: Record<string, unknown>) =>
            attrs.fontSize ? { style: `font-size: ${attrs.fontSize}` } : {}
        }
      }
    }]
  }
})

// ── Math extensions ───────────────────────────────────────────────────────────
function renderKatex(formula: string, displayMode: boolean): HTMLElement {
  const el = document.createElement(displayMode ? 'div' : 'span')
  try {
    katex.render(formula || '?', el, { throwOnError: false, displayMode })
  } catch {
    el.textContent = formula
  }
  return el
}

const MathInline = TiptapNode.create({
  name: 'mathInline',
  group: 'inline',
  inline: true,
  atom: true,
  addAttributes() {
    return { formula: { default: '' } }
  },
  addStorage() {
    return {
      markdown: {
        serialize(state: any, node: any) {
          const f = node.attrs.formula.replace(/&/g, '&amp;').replace(/"/g, '&quot;')
          state.write(`<span data-type="math-inline" data-formula="${f}"></span>`)
        }
      }
    }
  },
  parseHTML() {
    return [{ tag: 'span[data-type="math-inline"]', getAttrs: (el) => ({ formula: (el as unknown as HTMLElement).getAttribute('data-formula') }) }]
  },
  renderHTML({ node }) {
    return ['span', { 'data-type': 'math-inline', 'data-formula': node.attrs.formula }]
  },
  addNodeView() {
    return ({ node }) => {
      const dom = document.createElement('span')
      dom.classList.add('math-inline-node')
      dom.title = node.attrs.formula
      const rendered = renderKatex(node.attrs.formula, false)
      dom.appendChild(rendered)
      return { dom }
    }
  }
})

const MathBlock = TiptapNode.create({
  name: 'mathBlock',
  group: 'block',
  atom: true,
  addAttributes() {
    return { formula: { default: '' } }
  },
  addStorage() {
    return {
      markdown: {
        serialize(state: any, node: any) {
          const f = node.attrs.formula.replace(/&/g, '&amp;').replace(/"/g, '&quot;')
          state.write(`<div data-type="math-block" data-formula="${f}"></div>`)
          state.closeBlock(node)
        }
      }
    }
  },
  parseHTML() {
    return [{ tag: 'div[data-type="math-block"]', getAttrs: (el) => ({ formula: (el as unknown as HTMLElement).getAttribute('data-formula') }) }]
  },
  renderHTML({ node }) {
    return ['div', { 'data-type': 'math-block', 'data-formula': node.attrs.formula, class: 'math-block-node' }]
  },
  addNodeView() {
    return ({ node }) => {
      const dom = document.createElement('div')
      dom.classList.add('math-block-node')
      dom.title = node.attrs.formula
      const rendered = renderKatex(node.attrs.formula, true)
      dom.appendChild(rendered)
      return { dom }
    }
  }
})

// ── Alignment-aware Paragraph & Heading (serialise to HTML when not left-aligned) ──
function alignedMarkdownSerialize(state: any, node: any, defaultFn: () => void) {
  const align = node.attrs.textAlign
  if (align && align !== 'left') {
    const html = getHTMLFromFragment(PmFragment.from(node), node.type.schema)
    state.write(html.trim())
    state.closeBlock(node)
  } else {
    defaultFn()
  }
}

const AlignedParagraph = Paragraph.extend({
  addStorage() {
    return {
      markdown: {
        serialize(state: any, node: any) {
          alignedMarkdownSerialize(state, node, () => {
            state.renderInline(node)
            state.closeBlock(node)
          })
        }
      }
    }
  }
})

const AlignedHeading = Heading.extend({
  addStorage() {
    return {
      markdown: {
        serialize(state: any, node: any) {
          alignedMarkdownSerialize(state, node, () => {
            state.write(state.repeat('#', node.attrs.level) + ' ')
            state.renderInline(node)
            state.closeBlock(node)
          })
        }
      }
    }
  }
})

// ── Form state ────────────────────────────────────────────────────────────────
const form = reactive({ title: '', description: '', categoryName: '', coverUrl: '' })
const saving = ref(false)
const saveError = ref<string | null>(null)
const categories = ref<CategoryEntity[]>([])
getCategories().then((cats) => { categories.value = cats }).catch(() => {})

// ── File inputs ───────────────────────────────────────────────────────────────
const coverInput = ref<HTMLInputElement | null>(null)
const imageInput = ref<HTMLInputElement | null>(null)
const coverUploading = ref(false)
const imageUploading = ref(false)

// ── Word count ────────────────────────────────────────────────────────────────
const wordCount = ref({ words: 0, chars: 0 })

// ── Link dialog ───────────────────────────────────────────────────────────────
const showLinkDialog = ref(false)
const linkHref = ref('')
const linkInputRef = ref<HTMLInputElement | null>(null)

function openLinkDialog() {
  linkHref.value = editor.value?.getAttributes('link').href ?? ''
  showLinkDialog.value = true
  nextTick(() => linkInputRef.value?.focus())
}
function applyLink() {
  if (linkHref.value.trim()) {
    let href = linkHref.value.trim()
    if (!/^https?:\/\//i.test(href)) href = 'https://' + href
    editor.value?.chain().focus().setLink({ href }).run()
  } else {
    editor.value?.chain().focus().unsetLink().run()
  }
  showLinkDialog.value = false
  linkHref.value = ''
}
function cancelLink() {
  showLinkDialog.value = false
  linkHref.value = ''
  editor.value?.commands.focus()
}

// ── Math dialog ───────────────────────────────────────────────────────────────
const showMathDialog = ref(false)
const mathFormula = ref('')
const mathMode = ref<'inline' | 'block'>('inline')
const mathInputRef = ref<HTMLTextAreaElement | null>(null)
const isEditingMath = ref(false)

const mathPreview = computed(() => {
  if (!mathFormula.value.trim()) return ''
  try {
    return katex.renderToString(mathFormula.value, {
      throwOnError: false,
      displayMode: mathMode.value === 'block'
    })
  } catch {
    return `<span style="color:#ef4444;font-size:12px">Ошибка формулы</span>`
  }
})

const MATH_TEMPLATES = [
  { label: 'Дробь', tip: '\\frac{a}{b}', insert: '\\frac{a}{b}' },
  { label: '√ Корень', tip: '\\sqrt{x}', insert: '\\sqrt{x}' },
  { label: 'n√ Корень n', tip: '\\sqrt[n]{x}', insert: '\\sqrt[n]{x}' },
  { label: 'Степень', tip: 'x^{n}', insert: 'x^{n}' },
  { label: 'Индекс', tip: 'x_{i}', insert: 'x_{i}' },
  { label: '∑ Сумма', tip: '\\sum_{i=0}^{n}', insert: '\\sum_{i=0}^{n} x_i' },
  { label: '∏ Произведение', tip: '\\prod_{i=1}^{n}', insert: '\\prod_{i=1}^{n} x_i' },
  { label: '∫ Интеграл', tip: '\\int_{a}^{b}', insert: '\\int_{a}^{b} f(x)\\,dx' },
  { label: '∬ Двойной ∫', tip: '\\iint', insert: '\\iint_{D} f(x,y)\\,dx\\,dy' },
  { label: 'Предел', tip: '\\lim', insert: '\\lim_{x \\to \\infty} f(x)' },
  { label: '∂ Частная пр.', tip: '\\frac{\\partial f}{\\partial x}', insert: '\\frac{\\partial f}{\\partial x}' },
  { label: '∇ Набла', tip: '\\nabla', insert: '\\nabla f' },
  { label: '∞ Бесконечность', tip: '\\infty', insert: '\\infty' },
  { label: 'α Альфа', tip: '\\alpha', insert: '\\alpha' },
  { label: 'β Бета', tip: '\\beta', insert: '\\beta' },
  { label: 'γ Гамма', tip: '\\gamma', insert: '\\gamma' },
  { label: 'Δ Дельта', tip: '\\Delta', insert: '\\Delta' },
  { label: 'ε Эпсилон', tip: '\\varepsilon', insert: '\\varepsilon' },
  { label: 'θ Тета', tip: '\\theta', insert: '\\theta' },
  { label: 'λ Лямбда', tip: '\\lambda', insert: '\\lambda' },
  { label: 'μ Мю', tip: '\\mu', insert: '\\mu' },
  { label: 'π Пи', tip: '\\pi', insert: '\\pi' },
  { label: 'σ Сигма', tip: '\\sigma', insert: '\\sigma' },
  { label: 'φ Фи', tip: '\\varphi', insert: '\\varphi' },
  { label: 'ω Омега', tip: '\\omega', insert: '\\omega' },
  { label: '∈ Принадлежит', tip: '\\in', insert: '\\in' },
  { label: '⊆ Подмножество', tip: '\\subseteq', insert: '\\subseteq' },
  { label: '∪ Объединение', tip: '\\cup', insert: '\\cup' },
  { label: '∩ Пересечение', tip: '\\cap', insert: '\\cap' },
  { label: '± Плюс-минус', tip: '\\pm', insert: '\\pm' },
  { label: '× Умножить', tip: '\\times', insert: '\\times' },
  { label: '÷ Делить', tip: '\\div', insert: '\\div' },
  { label: '≈ Прибл. равно', tip: '\\approx', insert: '\\approx' },
  { label: '≠ Не равно', tip: '\\neq', insert: '\\neq' },
  { label: '≤ Меньше равно', tip: '\\leq', insert: '\\leq' },
  { label: '≥ Больше равно', tip: '\\geq', insert: '\\geq' },
  { label: 'Вектор', tip: '\\vec{v}', insert: '\\vec{v}' },
  { label: 'Норма', tip: '\\|x\\|', insert: '\\|x\\|' },
  { label: 'Матрица', tip: '\\begin{pmatrix}a&b\\\\c&d\\end{pmatrix}', insert: '\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}' },
  { label: 'Система ур.', tip: '\\begin{cases}...\\end{cases}', insert: '\\begin{cases} ax + by = c \\\\ dx + ey = f \\end{cases}' },
  { label: 'Скобки', tip: '\\left( \\right)', insert: '\\left( x \\right)' },
  { label: 'Абс. значение', tip: '\\left| \\right|', insert: '\\left| x \\right|' },
]

function openMathDialog(mode: 'inline' | 'block' = 'inline') {
  mathMode.value = mode
  isEditingMath.value = false

  // If a math node is currently selected, pre-populate for editing
  const ed = editor.value
  if (ed) {
    const sel = ed.state.selection as any
    if (sel.node) {
      if (sel.node.type.name === 'mathInline') {
        mathFormula.value = sel.node.attrs.formula
        mathMode.value = 'inline'
        isEditingMath.value = true
      } else if (sel.node.type.name === 'mathBlock') {
        mathFormula.value = sel.node.attrs.formula
        mathMode.value = 'block'
        isEditingMath.value = true
      } else {
        mathFormula.value = ''
      }
    } else {
      mathFormula.value = ''
    }
  }

  showMathDialog.value = true
  nextTick(() => mathInputRef.value?.focus())
}

function insertTemplate(tpl: string) {
  const el = mathInputRef.value
  if (!el) { mathFormula.value += tpl; return }
  const start = el.selectionStart ?? mathFormula.value.length
  const end = el.selectionEnd ?? mathFormula.value.length
  mathFormula.value = mathFormula.value.slice(0, start) + tpl + mathFormula.value.slice(end)
  nextTick(() => {
    el.focus()
    el.setSelectionRange(start + tpl.length, start + tpl.length)
  })
}

function applyMath() {
  const formula = mathFormula.value.trim()
  if (!formula) { closeMathDialog(); return }

  const ed = editor.value
  if (!ed) return

  const nodeType = mathMode.value === 'inline' ? 'mathInline' : 'mathBlock'
  const sel = ed.state.selection as any

  if (isEditingMath.value && sel.node) {
    ed.chain().focus().deleteSelection().insertContent({ type: nodeType, attrs: { formula } }).run()
  } else {
    ed.chain().focus().insertContent({ type: nodeType, attrs: { formula } }).run()
  }
  closeMathDialog()
}

function closeMathDialog() {
  showMathDialog.value = false
  mathFormula.value = ''
  isEditingMath.value = false
  editor.value?.commands.focus()
}

// ── Color pickers ─────────────────────────────────────────────────────────────
const showTextColorPicker = ref(false)
const showHighlightPicker = ref(false)
const textColorRef = ref<HTMLElement | null>(null)
const highlightRef = ref<HTMLElement | null>(null)

const TEXT_COLORS = [
  '#000000', '#1f2937', '#374151', '#6b7280', '#9ca3af', '#d1d5db', '#ffffff',
  '#7f1d1d', '#dc2626', '#ef4444', '#f97316', '#f59e0b', '#eab308', '#fbbf24',
  '#065f46', '#16a34a', '#22c55e', '#0d9488', '#0284c7', '#3b82f6', '#6366f1',
  '#7e22ce', '#a855f7', '#be185d', '#ec4899', '#f43f5e',
]
const HIGHLIGHT_COLORS = [
  '#fef08a', '#bbf7d0', '#bfdbfe', '#fbcfe8',
  '#fed7aa', '#e9d5ff', '#fecaca', '#cffafe',
  '#f3f4f6', '#fde68a', '#d1fae5', '#dbeafe',
]

function onTextColorDocClick(e: MouseEvent) {
  if (!textColorRef.value?.contains(e.target as Node)) showTextColorPicker.value = false
}
function onHighlightDocClick(e: MouseEvent) {
  if (!highlightRef.value?.contains(e.target as Node)) showHighlightPicker.value = false
}
watch(showTextColorPicker, (v) => {
  if (v) document.addEventListener('click', onTextColorDocClick, true)
  else document.removeEventListener('click', onTextColorDocClick, true)
})
watch(showHighlightPicker, (v) => {
  if (v) document.addEventListener('click', onHighlightDocClick, true)
  else document.removeEventListener('click', onHighlightDocClick, true)
})

// ── Font options ──────────────────────────────────────────────────────────────
const selectedFontSize = ref('')
const selectedFontFamily = ref('')

const fontFamilies = [
  { label: 'По умолчанию', value: '' },
  { label: 'Inter', value: 'Inter, sans-serif' },
  { label: 'Roboto', value: 'Roboto, sans-serif' },
  { label: 'Open Sans', value: '"Open Sans", sans-serif' },
  { label: 'Georgia', value: 'Georgia, serif' },
  { label: 'Playfair Display', value: '"Playfair Display", serif' },
  { label: 'Merriweather', value: 'Merriweather, serif' },
  { label: 'Courier New', value: '"Courier New", Courier, monospace' },
  { label: 'Fira Code', value: '"Fira Code", monospace' },
  { label: 'IBM Plex Mono', value: '"IBM Plex Mono", monospace' },
]

const fontSizes = [
  { label: 'Мини (10px)', value: '0.625rem' },
  { label: 'Маленький (12px)', value: '0.75rem' },
  { label: 'Небольшой (14px)', value: '0.875rem' },
  { label: 'Обычный (16px)', value: '1rem' },
  { label: 'Чуть крупнее (18px)', value: '1.125rem' },
  { label: 'Средний (20px)', value: '1.25rem' },
  { label: 'Крупный (24px)', value: '1.5rem' },
  { label: 'Большой (28px)', value: '1.75rem' },
  { label: 'Очень большой (32px)', value: '2rem' },
  { label: 'Огромный (40px)', value: '2.5rem' },
]

function applyFontSize(size: string) {
  if (!size) editor.value?.chain().focus().setMark('textStyle', { fontSize: null }).run()
  else editor.value?.chain().focus().setMark('textStyle', { fontSize: size }).run()
}
function applyFontFamily(family: string) {
  if (!family) editor.value?.chain().focus().unsetFontFamily().run()
  else editor.value?.chain().focus().setFontFamily(family).run()
}

// ── Editor ────────────────────────────────────────────────────────────────────
const editorReady = ref(false)

const editor = useEditor({
  extensions: [
    StarterKit.configure({ heading: false, paragraph: false }),
    AlignedParagraph,
    AlignedHeading.configure({ levels: [1, 2, 3] }),
    Underline,
    TextStyle,
    FontFamily,
    FontSize,
    Color,
    Highlight.configure({ multicolor: true }),
    Superscript,
    Subscript,
    MathInline,
    MathBlock,
    Image.configure({ inline: false, allowBase64: false }),
    Link.configure({
      openOnClick: false,
      HTMLAttributes: { rel: 'noopener noreferrer', class: 'editor-link' }
    }),
    Table.configure({ resizable: false }),
    TableRow,
    TableHeader,
    TableCell,
    Placeholder.configure({ placeholder: 'Напишите что-нибудь...' }),
    TextAlign.configure({ types: ['heading', 'paragraph'] }),
    TaskList,
    TaskItem.configure({ nested: true }),
    Markdown.configure({ html: true, tightLists: true, breaks: true, transformPastedText: true }),
  ],
  content: '',
  onCreate: () => {
    editorReady.value = true
    if (props.initialData) fillFromData(props.initialData)
  },
  onUpdate: ({ editor }) => {
    const text = editor.state.doc.textContent
    wordCount.value = {
      words: text.trim() ? text.trim().split(/\s+/).length : 0,
      chars: text.length,
    }
  },
  onSelectionUpdate: ({ editor }) => {
    const sel = editor.state.selection as any
    if (sel.node && (sel.node.type.name === 'mathInline' || sel.node.type.name === 'mathBlock')) {
      mathFormula.value = sel.node.attrs.formula
      mathMode.value = sel.node.type.name === 'mathInline' ? 'inline' : 'block'
      isEditingMath.value = true
      showMathDialog.value = true
    }
  },
})

onBeforeUnmount(() => {
  editor.value?.destroy()
  document.removeEventListener('click', onTextColorDocClick, true)
  document.removeEventListener('click', onHighlightDocClick, true)
})

watch(() => props.initialData, (data) => {
  if (data && editorReady.value) fillFromData(data)
})

// Convert $...$  and $$...$$ (from older saves) to data-type HTML so parseHTML recognises them
function preprocessMathForEditor(text: string): string {
  text = text.replace(/\$\$([\s\S]+?)\$\$/g, (_, formula) => {
    const f = formula.trim().replace(/&/g, '&amp;').replace(/"/g, '&quot;')
    return `<div data-type="math-block" data-formula="${f}"></div>`
  })
  text = text.replace(/\$([^$\n]+?)\$/g, (_, formula) => {
    const f = formula.trim().replace(/&/g, '&amp;').replace(/"/g, '&quot;')
    return `<span data-type="math-inline" data-formula="${f}"></span>`
  })
  return text
}

function fillFromData(data: ArticleResponse) {
  form.title = data.title ?? ''
  form.description = data.description ?? ''
  form.categoryName = data.category?.name ?? ''
  form.coverUrl = data.image ?? ''
  editor.value?.commands.setContent(preprocessMathForEditor(data.text ?? ''))
}

// ── Toolbar helpers ───────────────────────────────────────────────────────────
function isActive(name: string, attrs?: Record<string, unknown>) {
  return editor.value?.isActive(name, attrs) ?? false
}
function btnCls(name: string, attrs?: Record<string, unknown>) {
  return isActive(name, attrs) ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
}

// ── Image upload ──────────────────────────────────────────────────────────────
async function handleCoverFile(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  coverUploading.value = true
  saveError.value = null
  try {
    form.coverUrl = await uploadImage(file)
  } catch (err) {
    saveError.value = `Не удалось загрузить обложку: ${(err as Error).message}`
  } finally {
    coverUploading.value = false
    if (coverInput.value) coverInput.value.value = ''
  }
}
async function handleInlineImage(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  imageUploading.value = true
  saveError.value = null
  try {
    const url = await uploadImage(file)
    editor.value?.chain().focus().setImage({ src: url, alt: file.name.replace(/\.[^.]+$/, '') }).run()
  } catch (err) {
    saveError.value = `Не удалось загрузить изображение: ${(err as Error).message}`
  } finally {
    imageUploading.value = false
    if (imageInput.value) imageInput.value.value = ''
  }
}

// ── Save ──────────────────────────────────────────────────────────────────────
async function save(draft: boolean) {
  saveError.value = null
  if (!form.title.trim()) { saveError.value = 'Введите заголовок'; return }

  const payload: ArticleRequest = {
    title: form.title.trim(),
    description: form.description.trim(),
    text: editor.value?.storage.markdown.getMarkdown() ?? '',
    image: form.coverUrl || null,
    categoryName: form.categoryName || (categories.value[0]?.name ?? 'general'),
    draft,
  }

  saving.value = true
  try {
    const saved = props.articleId
      ? await updateArticle(props.articleId, payload)
      : await createArticle(payload)
    if (draft) router.push({ name: 'publish', query: { tab: 'drafts' } })
    else router.push({ name: 'article', params: { id: saved.articleId } })
  } catch {
    saveError.value = 'Не удалось сохранить статью'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="max-w-3xl mx-auto">

    <!-- Hidden file inputs -->
    <input ref="coverInput" type="file" accept="image/*" class="hidden" @change="handleCoverFile" />
    <input ref="imageInput" type="file" accept="image/*" class="hidden" @change="handleInlineImage" />

    <!-- Title -->
    <input
      v-model="form.title"
      type="text"
      placeholder="Заголовок статьи"
      class="w-full text-3xl font-bold text-gray-900 placeholder-gray-300 border-0 outline-none mb-6 bg-transparent"
    />

    <!-- Cover image -->
    <div class="mb-6">
      <div v-if="form.coverUrl" class="relative group rounded-xl overflow-hidden">
        <img :src="form.coverUrl" alt="Обложка" class="w-full h-52 object-cover" />
        <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-3">
          <button @click="coverInput?.click()" class="px-3 py-1.5 text-sm font-medium bg-white text-gray-800 rounded-lg hover:bg-gray-100">Заменить</button>
          <button @click="form.coverUrl = ''" class="px-3 py-1.5 text-sm font-medium bg-white text-red-600 rounded-lg hover:bg-red-50">Удалить</button>
        </div>
      </div>
      <button
        v-else @click="coverInput?.click()" :disabled="coverUploading"
        class="w-full h-28 border-2 border-dashed border-gray-200 rounded-xl text-sm text-gray-400
               hover:border-blue-300 hover:text-blue-500 transition-colors flex flex-col items-center justify-center gap-1"
      >
        <div v-if="coverUploading" class="w-5 h-5 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
        <svg v-else class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
        </svg>
        <span>{{ coverUploading ? 'Загрузка...' : 'Добавить обложку' }}</span>
      </button>
    </div>

    <!-- Metadata row -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 mb-6">
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium text-gray-500">Категория</label>
        <select v-model="form.categoryName" class="px-3 py-2 rounded-lg border border-gray-200 text-sm text-gray-700 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 bg-white">
          <option value="">— выберите —</option>
          <option v-for="cat in categories" :key="cat.id" :value="cat.name">{{ cat.name }}</option>
        </select>
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium text-gray-500">Краткое описание</label>
        <input v-model="form.description" type="text" placeholder="Несколько предложений о статье"
               class="px-3 py-2 rounded-lg border border-gray-200 text-sm text-gray-700 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100" />
      </div>
    </div>

    <!-- Editor card -->
    <div class="border border-gray-200 rounded-xl overflow-hidden">

      <!-- ── Toolbar row 1 ── -->
      <div class="flex flex-wrap items-center gap-0.5 px-2 py-1.5 bg-gray-50 border-b border-gray-100">

        <button @click="editor?.chain().focus().toggleBold().run()" :class="['toolbar-btn', btnCls('bold')]" title="Жирный (Ctrl+B)">
          <strong class="text-sm leading-none">B</strong>
        </button>
        <button @click="editor?.chain().focus().toggleItalic().run()" :class="['toolbar-btn', btnCls('italic')]" title="Курсив (Ctrl+I)">
          <em class="text-sm leading-none">I</em>
        </button>
        <button @click="editor?.chain().focus().toggleUnderline().run()" :class="['toolbar-btn', btnCls('underline')]" title="Подчёркнутый">
          <span class="text-sm underline leading-none">U</span>
        </button>
        <button @click="editor?.chain().focus().toggleStrike().run()" :class="['toolbar-btn', btnCls('strike')]" title="Зачёркнутый">
          <span class="text-sm line-through leading-none">S</span>
        </button>
        <button @click="editor?.chain().focus().toggleSuperscript().run()" :class="['toolbar-btn text-xs', btnCls('superscript')]" title="Надстрочный">
          x<sup class="text-[9px]">²</sup>
        </button>
        <button @click="editor?.chain().focus().toggleSubscript().run()" :class="['toolbar-btn text-xs', btnCls('subscript')]" title="Подстрочный">
          x<sub class="text-[9px]">₂</sub>
        </button>
        <button @click="editor?.chain().focus().clearNodes().unsetAllMarks().run()"
                class="toolbar-btn text-gray-500 hover:bg-red-50 hover:text-red-500" title="Очистить форматирование">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>

        <div class="w-px h-5 bg-gray-200 mx-0.5" />

        <button @click="editor?.chain().focus().toggleHeading({ level: 1 }).run()" :class="['toolbar-btn text-xs font-bold', btnCls('heading', { level: 1 })]">H1</button>
        <button @click="editor?.chain().focus().toggleHeading({ level: 2 }).run()" :class="['toolbar-btn text-xs font-bold', btnCls('heading', { level: 2 })]">H2</button>
        <button @click="editor?.chain().focus().toggleHeading({ level: 3 }).run()" :class="['toolbar-btn text-xs font-bold', btnCls('heading', { level: 3 })]">H3</button>

        <div class="w-px h-5 bg-gray-200 mx-0.5" />

        <button @click="editor?.chain().focus().toggleBulletList().run()" :class="['toolbar-btn', btnCls('bulletList')]" title="Маркированный список">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/></svg>
        </button>
        <button @click="editor?.chain().focus().toggleOrderedList().run()" :class="['toolbar-btn', btnCls('orderedList')]" title="Нумерованный список">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h10M7 16h10M3 8h.01M3 12h.01M3 16h.01"/></svg>
        </button>
        <button @click="editor?.chain().focus().toggleTaskList().run()" :class="['toolbar-btn', btnCls('taskList')]" title="Список задач">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/></svg>
        </button>
        <button @click="editor?.chain().focus().toggleBlockquote().run()" :class="['toolbar-btn', btnCls('blockquote')]" title="Цитата">
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M10 7H6C4.9 7 4 7.9 4 9v4c0 1.1.9 2 2 2h2l-2 4h2l2-4V9c0-1.1-.9-2-2-2zm8 0h-4c-1.1 0-2 .9-2 2v4c0 1.1.9 2 2 2h2l-2 4h2l2-4V9c0-1.1-.9-2-2-2z"/></svg>
        </button>
        <button @click="editor?.chain().focus().toggleCodeBlock().run()" :class="['toolbar-btn', btnCls('codeBlock')]" title="Блок кода">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/></svg>
        </button>
        <button @click="editor?.chain().focus().setHorizontalRule().run()" class="toolbar-btn text-gray-600 hover:bg-gray-100" title="Горизонтальная линия">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 12h16"/></svg>
        </button>

        <div class="w-px h-5 bg-gray-200 mx-0.5" />

        <!-- Link -->
        <div class="relative">
          <button @click="openLinkDialog" :class="['toolbar-btn', btnCls('link')]" title="Ссылка">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/></svg>
          </button>
          <div v-if="showLinkDialog" class="absolute top-10 left-0 z-30 bg-white border border-gray-200 rounded-xl shadow-xl p-3 w-72">
            <p class="text-xs font-medium text-gray-500 mb-2">Вставить ссылку</p>
            <div class="flex gap-2">
              <input ref="linkInputRef" v-model="linkHref" type="text" placeholder="https://example.com"
                     class="flex-1 px-2 py-1.5 text-sm border border-gray-200 rounded-lg outline-none focus:border-blue-400"
                     @keydown.enter.prevent="applyLink" @keydown.escape="cancelLink" />
              <button @click="applyLink" class="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700">ОК</button>
            </div>
            <div class="flex gap-3 mt-1.5">
              <button @click="cancelLink" class="text-xs text-gray-400 hover:text-gray-600">Отмена</button>
              <button v-if="editor?.isActive('link')" @click="editor?.chain().focus().unsetLink().run(); showLinkDialog = false" class="text-xs text-red-400 hover:text-red-600">Удалить ссылку</button>
            </div>
          </div>
        </div>

        <!-- Image -->
        <button @click="imageInput?.click()" :disabled="imageUploading" class="toolbar-btn text-gray-600 hover:bg-gray-100" title="Вставить изображение">
          <div v-if="imageUploading" class="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
          <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
        </button>

        <!-- Math (inline) -->
        <button @click="openMathDialog('inline')" :class="['toolbar-btn font-serif text-base font-bold', isActive('mathInline') ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100']" title="Формула в строке ($ … $)">
          ∑
        </button>
        <!-- Math (block) -->
        <button @click="openMathDialog('block')" :class="['toolbar-btn font-serif text-base font-bold', isActive('mathBlock') ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100']" title="Формула в отдельном блоке ($$ … $$)">
          ∫
        </button>

        <div class="w-px h-5 bg-gray-200 mx-0.5" />

        <button @click="editor?.chain().focus().undo().run()" class="toolbar-btn text-gray-600 hover:bg-gray-100" title="Отменить (Ctrl+Z)">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 010 16H3m0-16l4-4M3 10l4 4"/></svg>
        </button>
        <button @click="editor?.chain().focus().redo().run()" class="toolbar-btn text-gray-600 hover:bg-gray-100" title="Повторить (Ctrl+Y)">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 10H11a8 8 0 000 16h10m0-16l-4-4m4 4l-4 4"/></svg>
        </button>
      </div>

      <!-- ── Toolbar row 2 ── -->
      <div class="flex flex-wrap items-center gap-1.5 px-3 py-1.5 bg-gray-50 border-b border-gray-200">

        <select v-model="selectedFontFamily" @change="applyFontFamily(selectedFontFamily)"
                class="text-xs px-2 py-1 border border-gray-200 rounded-md bg-white text-gray-600 outline-none focus:border-blue-400 cursor-pointer max-w-[130px]">
          <option v-for="f in fontFamilies" :key="f.value" :value="f.value" :style="f.value ? { fontFamily: f.value } : {}">{{ f.label }}</option>
        </select>

        <select v-model="selectedFontSize" @change="applyFontSize(selectedFontSize)"
                class="text-xs px-2 py-1 border border-gray-200 rounded-md bg-white text-gray-600 outline-none focus:border-blue-400 cursor-pointer max-w-[140px]">
          <option value="">Размер</option>
          <option v-for="s in fontSizes" :key="s.value" :value="s.value">{{ s.label }}</option>
        </select>

        <div class="w-px h-5 bg-gray-200" />

        <!-- Text color -->
        <div ref="textColorRef" class="relative">
          <button @click="showTextColorPicker = !showTextColorPicker; showHighlightPicker = false"
                  class="toolbar-btn flex flex-col items-center justify-center gap-0.5 px-1.5" title="Цвет текста">
            <span class="text-sm font-bold leading-none" :style="{ color: editor?.getAttributes('textStyle').color || '#1f2937' }">A</span>
            <span class="w-4 h-[3px] rounded-full" :style="{ background: editor?.getAttributes('textStyle').color || '#1f2937' }" />
          </button>
          <div v-if="showTextColorPicker" class="absolute top-10 left-0 z-30 bg-white border border-gray-200 rounded-xl shadow-xl p-3 w-52">
            <p class="text-xs text-gray-400 mb-2">Цвет текста</p>
            <div class="grid grid-cols-7 gap-1">
              <button v-for="color in TEXT_COLORS" :key="color"
                      @click="editor?.chain().focus().setColor(color).run(); showTextColorPicker = false"
                      class="w-6 h-6 rounded-md border border-gray-200 hover:scale-110 transition-transform"
                      :style="{ background: color }" :title="color" />
            </div>
            <button @click="editor?.chain().focus().unsetColor().run(); showTextColorPicker = false"
                    class="mt-2 text-xs text-gray-400 hover:text-gray-700 w-full text-left">× Сбросить цвет</button>
          </div>
        </div>

        <!-- Highlight -->
        <div ref="highlightRef" class="relative">
          <button @click="showHighlightPicker = !showHighlightPicker; showTextColorPicker = false"
                  class="toolbar-btn flex flex-col items-center justify-center gap-0.5 px-1.5" title="Цвет выделения">
            <span class="text-sm font-bold leading-none px-0.5 rounded-sm"
                  :style="{ background: editor?.getAttributes('highlight').color || '#fef08a' }">A</span>
            <span class="w-4 h-[3px] rounded-full" :style="{ background: editor?.getAttributes('highlight').color || '#fef08a' }" />
          </button>
          <div v-if="showHighlightPicker" class="absolute top-10 left-0 z-30 bg-white border border-gray-200 rounded-xl shadow-xl p-3 w-48">
            <p class="text-xs text-gray-400 mb-2">Выделение</p>
            <div class="grid grid-cols-6 gap-1">
              <button v-for="color in HIGHLIGHT_COLORS" :key="color"
                      @click="editor?.chain().focus().setHighlight({ color }).run(); showHighlightPicker = false"
                      class="w-6 h-6 rounded-md border border-gray-200 hover:scale-110 transition-transform"
                      :style="{ background: color }" :title="color" />
            </div>
            <button @click="editor?.chain().focus().unsetHighlight().run(); showHighlightPicker = false"
                    class="mt-2 text-xs text-gray-400 hover:text-gray-700 w-full text-left">× Убрать выделение</button>
          </div>
        </div>

        <div class="w-px h-5 bg-gray-200" />

        <button @click="editor?.chain().focus().setTextAlign('left').run()" :class="['toolbar-btn', btnCls('textAlign', { textAlign: 'left' })]" title="По левому краю">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h10M4 14h16M4 18h10"/></svg>
        </button>
        <button @click="editor?.chain().focus().setTextAlign('center').run()" :class="['toolbar-btn', btnCls('textAlign', { textAlign: 'center' })]" title="По центру">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M7 10h10M4 14h16M7 18h10"/></svg>
        </button>
        <button @click="editor?.chain().focus().setTextAlign('right').run()" :class="['toolbar-btn', btnCls('textAlign', { textAlign: 'right' })]" title="По правому краю">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M10 10h10M4 14h16M10 18h10"/></svg>
        </button>
        <button @click="editor?.chain().focus().setTextAlign('justify').run()" :class="['toolbar-btn', btnCls('textAlign', { textAlign: 'justify' })]" title="По ширине">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"/></svg>
        </button>

        <div class="w-px h-5 bg-gray-200" />

        <button @click="editor?.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()"
                class="toolbar-btn text-gray-600 hover:bg-gray-100 flex items-center gap-1 text-xs px-2" title="Вставить таблицу">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 14h18M10 3v18M6 3h12a1 1 0 011 1v16a1 1 0 01-1 1H6a1 1 0 01-1-1V4a1 1 0 011-1z"/></svg>
          Таблица
        </button>
        <template v-if="editor?.isActive('table')">
          <div class="w-px h-5 bg-gray-200" />
          <button @click="editor?.chain().focus().addColumnBefore().run()" class="toolbar-btn text-xs text-gray-600 hover:bg-gray-100 px-2">+кол</button>
          <button @click="editor?.chain().focus().addRowBefore().run()" class="toolbar-btn text-xs text-gray-600 hover:bg-gray-100 px-2">+стр</button>
          <button @click="editor?.chain().focus().deleteColumn().run()" class="toolbar-btn text-xs text-red-400 hover:bg-red-50 px-2">−кол</button>
          <button @click="editor?.chain().focus().deleteRow().run()" class="toolbar-btn text-xs text-red-400 hover:bg-red-50 px-2">−стр</button>
          <button @click="editor?.chain().focus().deleteTable().run()" class="toolbar-btn text-xs text-red-500 hover:bg-red-50 px-2 font-medium">✕ табл</button>
        </template>
      </div>

      <!-- ── Content area ── -->
      <div class="overflow-y-auto" style="min-height: 480px; max-height: 600px;">
        <EditorContent :editor="editor" class="editor-content h-full" />
      </div>

      <!-- ── Footer: word count ── -->
      <div class="flex items-center justify-end gap-4 px-4 py-1.5 bg-gray-50 border-t border-gray-100 text-xs text-gray-400">
        <span>{{ wordCount.words }} слов</span>
        <span>{{ wordCount.chars }} символов</span>
      </div>
    </div>

    <!-- ── Math dialog ── -->
    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-100 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div v-if="showMathDialog" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/30">
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">

          <!-- Header -->
          <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100">
            <div>
              <h3 class="text-base font-semibold text-gray-900">
                {{ isEditingMath ? 'Редактировать формулу' : 'Вставить формулу' }}
              </h3>
              <p class="text-xs text-gray-400 mt-0.5">LaTeX / KaTeX синтаксис</p>
            </div>
            <!-- Mode toggle -->
            <div class="flex gap-1 bg-gray-100 rounded-lg p-0.5 text-sm">
              <button @click="mathMode = 'inline'"
                      class="px-3 py-1 rounded-md font-medium transition-all"
                      :class="mathMode === 'inline' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'">
                ∑ Inline
              </button>
              <button @click="mathMode = 'block'"
                      class="px-3 py-1 rounded-md font-medium transition-all"
                      :class="mathMode === 'block' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'">
                ∫ Block
              </button>
            </div>
          </div>

          <div class="flex flex-1 min-h-0 overflow-hidden">

            <!-- Left: input + templates -->
            <div class="flex flex-col flex-1 min-w-0 border-r border-gray-100">
              <!-- LaTeX input -->
              <div class="p-4 border-b border-gray-100">
                <label class="text-xs font-medium text-gray-500 mb-1.5 block">LaTeX код</label>
                <textarea
                  ref="mathInputRef"
                  v-model="mathFormula"
                  rows="4"
                  placeholder="\frac{a}{b}, \sum_{i=0}^{n}, \int_a^b f(x)\,dx..."
                  class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 font-mono resize-none"
                  @keydown.enter.ctrl="applyMath"
                />
                <p class="text-xs text-gray-400 mt-1">Ctrl+Enter — применить</p>
              </div>

              <!-- Templates -->
              <div class="flex-1 overflow-y-auto p-4">
                <p class="text-xs font-medium text-gray-500 mb-2">Шаблоны (нажмите чтобы вставить)</p>
                <div class="flex flex-wrap gap-1.5">
                  <button
                    v-for="tpl in MATH_TEMPLATES"
                    :key="tpl.label"
                    @click="insertTemplate(tpl.insert)"
                    class="px-2 py-1 text-xs bg-gray-100 hover:bg-blue-50 hover:text-blue-700 text-gray-700 rounded-md transition-colors font-mono"
                    :title="tpl.tip"
                  >
                    {{ tpl.label }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Right: live preview -->
            <div class="w-64 flex-shrink-0 flex flex-col">
              <div class="p-4 border-b border-gray-100">
                <p class="text-xs font-medium text-gray-500 mb-2">Предпросмотр</p>
                <div
                  class="min-h-16 flex items-center justify-center p-3 bg-gray-50 rounded-lg border border-gray-100 overflow-x-auto"
                  :class="mathMode === 'block' ? 'text-center' : ''"
                >
                  <span v-if="!mathFormula.trim()" class="text-gray-300 text-xs">Введите формулу...</span>
                  <span v-else v-html="mathPreview" />
                </div>
              </div>

              <!-- Quick symbols -->
              <div class="p-4 flex-1 overflow-y-auto">
                <p class="text-xs font-medium text-gray-500 mb-2">Быстрый ввод</p>
                <div class="grid grid-cols-4 gap-1">
                  <button v-for="s in [
                    ['α','\\alpha'],['β','\\beta'],['γ','\\gamma'],['δ','\\delta'],
                    ['ε','\\varepsilon'],['θ','\\theta'],['λ','\\lambda'],['μ','\\mu'],
                    ['π','\\pi'],['σ','\\sigma'],['φ','\\varphi'],['ω','\\omega'],
                    ['∞','\\infty'],['∂','\\partial'],['∇','\\nabla'],['±','\\pm'],
                    ['×','\\times'],['÷','\\div'],['≈','\\approx'],['≠','\\neq'],
                    ['≤','\\leq'],['≥','\\geq'],['∈','\\in'],['∉','\\notin'],
                    ['⊆','\\subseteq'],['∪','\\cup'],['∩','\\cap'],['→','\\to'],
                  ] as const"
                    :key="s[0]"
                    @click="insertTemplate(s[1])"
                    class="h-8 flex items-center justify-center text-sm bg-gray-50 hover:bg-blue-50 hover:text-blue-700 rounded-md border border-gray-200 transition-colors"
                    :title="s[1]"
                  >
                    {{ s[0] }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="flex items-center justify-between px-5 py-3 border-t border-gray-100 bg-gray-50">
            <button @click="closeMathDialog" class="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 transition-colors">Отмена</button>
            <button @click="applyMath" class="px-5 py-2 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
              {{ isEditingMath ? 'Обновить' : 'Вставить' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Error -->
    <p v-if="saveError" class="mt-3 text-sm text-red-500 bg-red-50 px-3 py-2 rounded-lg">{{ saveError }}</p>

    <!-- Action buttons -->
    <div class="flex justify-end gap-3 mt-6">
      <button @click="save(true)" :disabled="saving"
              class="px-5 py-2.5 text-sm font-medium border border-gray-300 rounded-lg text-gray-700 hover:border-blue-400 hover:text-blue-600 disabled:opacity-50 transition-colors">
        {{ saving ? 'Сохранение...' : 'Сохранить черновик' }}
      </button>
      <button @click="save(false)" :disabled="saving"
              class="px-5 py-2.5 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-60 transition-colors">
        {{ saving ? 'Публикация...' : 'Опубликовать' }}
      </button>
    </div>

  </div>
</template>

<style scoped>
.toolbar-btn {
  @apply p-1.5 rounded-md transition-colors flex items-center justify-center min-w-[2rem] h-8 flex-shrink-0;
}

:deep(.ProseMirror) {
  @apply outline-none px-5 py-4;
  min-height: 480px;
  caret-color: #3b82f6;
  line-height: 1.75;
  font-size: 1rem;
}
:deep(.ProseMirror > * + *) { margin-top: 0.6em; }

:deep(.ProseMirror h1) { @apply text-3xl font-bold text-gray-900 mt-4 mb-1; }
:deep(.ProseMirror h2) { @apply text-2xl font-bold text-gray-900 mt-3 mb-1; }
:deep(.ProseMirror h3) { @apply text-xl font-semibold text-gray-900 mt-2 mb-1; }
:deep(.ProseMirror p)  { @apply text-gray-700; }

:deep(.ProseMirror ul)  { @apply list-disc pl-6 space-y-1; }
:deep(.ProseMirror ol)  { @apply list-decimal pl-6 space-y-1; }

/* Task list */
:deep(.ProseMirror ul[data-type="taskList"]) { list-style: none; padding-left: 0; }
:deep(.ProseMirror ul[data-type="taskList"] li) { display: flex; align-items: flex-start; gap: 8px; }
:deep(.ProseMirror ul[data-type="taskList"] li > label) { flex-shrink: 0; margin-top: 3px; cursor: pointer; }
:deep(.ProseMirror ul[data-type="taskList"] li > label input[type="checkbox"]) { width: 16px; height: 16px; cursor: pointer; accent-color: #3b82f6; }
:deep(.ProseMirror ul[data-type="taskList"] li > div) { flex: 1; }
:deep(.ProseMirror ul[data-type="taskList"] li[data-checked="true"] > div) { text-decoration: line-through; opacity: 0.55; }

:deep(.ProseMirror blockquote) { @apply border-l-4 border-blue-200 pl-4 text-gray-500 italic my-3; }

:deep(.ProseMirror pre) {
  background: #282c34; color: #abb2bf; border-radius: 0.5rem;
  padding: 1rem 1.25rem; overflow-x: auto; margin: 0.75rem 0;
  font-family: 'Fira Code', 'Consolas', 'Monaco', monospace; font-size: 0.875rem; line-height: 1.6;
}
:deep(.ProseMirror pre code) { color: inherit; background: transparent; padding: 0; border-radius: 0; font-size: inherit; }
:deep(.ProseMirror code) { @apply bg-gray-100 text-red-500 px-1.5 py-0.5 rounded text-sm font-mono; }

:deep(.ProseMirror hr) { border: none; border-top: 2px solid #e5e7eb; margin: 1.5rem 0; }
:deep(.ProseMirror img) { @apply max-w-full h-auto rounded-lg my-3; }
:deep(.ProseMirror a) { @apply text-blue-600 underline cursor-pointer; }

/* Math nodes */
:deep(.math-inline-node) {
  display: inline-block;
  cursor: pointer;
  padding: 0 2px;
  border-radius: 3px;
  background: #f0f7ff;
  border: 1px solid #bfdbfe;
  vertical-align: middle;
  transition: background 0.15s;
}
:deep(.math-inline-node:hover) { background: #dbeafe; }
:deep(.math-inline-node.ProseMirror-selectednode) { outline: 2px solid #3b82f6; background: #dbeafe; }

:deep(.math-block-node) {
  display: block;
  text-align: center;
  cursor: pointer;
  padding: 12px 16px;
  margin: 12px 0;
  border-radius: 8px;
  background: #f8faff;
  border: 1px solid #bfdbfe;
  transition: background 0.15s;
  overflow-x: auto;
}
:deep(.math-block-node:hover) { background: #dbeafe; }
:deep(.math-block-node.ProseMirror-selectednode) { outline: 2px solid #3b82f6; background: #dbeafe; }

/* Tables */
:deep(.ProseMirror table) { border-collapse: collapse; width: 100%; margin: 0.75rem 0; font-size: 0.9rem; }
:deep(.ProseMirror th) { @apply bg-gray-50 font-semibold text-gray-700; border: 1px solid #e5e7eb; padding: 0.5rem 0.75rem; text-align: left; }
:deep(.ProseMirror td) { border: 1px solid #e5e7eb; padding: 0.5rem 0.75rem; vertical-align: top; }
:deep(.ProseMirror .selectedCell) { @apply bg-blue-50; }

:deep(.ProseMirror p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder); @apply text-gray-300; float: left; height: 0; pointer-events: none;
}
:deep(.ProseMirror sup) { font-size: 0.7em; vertical-align: super; }
:deep(.ProseMirror sub) { font-size: 0.7em; vertical-align: sub; }
</style>
