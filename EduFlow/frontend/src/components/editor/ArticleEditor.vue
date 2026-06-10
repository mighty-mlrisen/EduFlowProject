<script setup lang="ts">
import { ref, reactive, watch, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import { Extension } from '@tiptap/core'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import TextStyle from '@tiptap/extension-text-style'
import FontFamily from '@tiptap/extension-font-family'
import Image from '@tiptap/extension-image'
import Link from '@tiptap/extension-link'
import Placeholder from '@tiptap/extension-placeholder'
import Table from '@tiptap/extension-table'
import TableRow from '@tiptap/extension-table-row'
import TableCell from '@tiptap/extension-table-cell'
import TableHeader from '@tiptap/extension-table-header'
import TextAlign from '@tiptap/extension-text-align'
import { Markdown } from 'tiptap-markdown'
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

// ── Form state ───────────────────────────────────────────────────────────────
const form = reactive({
  title: '',
  description: '',
  categoryName: '',
  coverUrl: ''
})
const saving = ref(false)
const saveError = ref<string | null>(null)
const categories = ref<CategoryEntity[]>([])

getCategories().then((cats) => { categories.value = cats }).catch(() => {})

// ── File inputs ───────────────────────────────────────────────────────────────
const coverInput = ref<HTMLInputElement | null>(null)
const imageInput = ref<HTMLInputElement | null>(null)
const coverUploading = ref(false)
const imageUploading = ref(false)

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

// ── Toolbar state ─────────────────────────────────────────────────────────────
const selectedFontSize = ref('')
const selectedFontFamily = ref('')

const fontSizes = [
  { label: 'Мелкий', value: '0.8rem' },
  { label: 'Обычный', value: '1rem' },
  { label: 'Большой', value: '1.2rem' },
  { label: 'Крупный', value: '1.5rem' },
  { label: 'Огромный', value: '2rem' }
]

const fontFamilies = [
  { label: 'По умолчанию', value: '' },
  { label: 'Inter', value: 'Inter, sans-serif' },
  { label: 'Georgia', value: 'Georgia, serif' },
  { label: 'Monospace', value: '"Courier New", Courier, monospace' }
]

function applyFontSize(size: string) {
  if (!size) {
    editor.value?.chain().focus().setMark('textStyle', { fontSize: null }).run()
  } else {
    editor.value?.chain().focus().setMark('textStyle', { fontSize: size }).run()
  }
}

function applyFontFamily(family: string) {
  if (!family) {
    editor.value?.chain().focus().unsetFontFamily().run()
  } else {
    editor.value?.chain().focus().setFontFamily(family).run()
  }
}

// ── Editor ────────────────────────────────────────────────────────────────────
const editorReady = ref(false)

const editor = useEditor({
  extensions: [
    StarterKit.configure({ heading: { levels: [1, 2, 3] } }),
    Underline,
    TextStyle,
    FontFamily,
    FontSize,
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
    Markdown.configure({ html: true, tightLists: true, breaks: true, transformPastedText: true })
  ],
  content: '',
  onCreate: () => {
    editorReady.value = true
    if (props.initialData) fillFromData(props.initialData)
  }
})

onBeforeUnmount(() => editor.value?.destroy())

watch(() => props.initialData, (data) => {
  if (data && editorReady.value) fillFromData(data)
})

function fillFromData(data: ArticleResponse) {
  form.title = data.title ?? ''
  form.description = data.description ?? ''
  form.categoryName = data.category?.name ?? ''
  form.coverUrl = data.image ?? ''
  editor.value?.commands.setContent(data.text ?? '')
}

// ── Toolbar helpers ───────────────────────────────────────────────────────────
function isActive(name: string, attrs?: Record<string, unknown>) {
  return editor.value?.isActive(name, attrs) ?? false
}

function btnCls(name: string, attrs?: Record<string, unknown>) {
  return isActive(name, attrs)
    ? 'bg-blue-100 text-blue-700'
    : 'text-gray-600 hover:bg-gray-100'
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
  if (!form.title.trim()) {
    saveError.value = 'Введите заголовок'
    return
  }

  const payload: ArticleRequest = {
    title: form.title.trim(),
    description: form.description.trim(),
    text: editor.value?.storage.markdown.getMarkdown() ?? '',
    image: form.coverUrl || null,
    categoryName: form.categoryName || (categories.value[0]?.name ?? 'general'),
    draft
  }

  saving.value = true
  try {
    const saved = props.articleId
      ? await updateArticle(props.articleId, payload)
      : await createArticle(payload)

    if (draft) {
      router.push({ name: 'publish', query: { tab: 'drafts' } })
    } else {
      router.push({ name: 'article', params: { id: saved.articleId } })
    }
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
          <button
            @click="coverInput?.click()"
            class="px-3 py-1.5 text-sm font-medium bg-white text-gray-800 rounded-lg hover:bg-gray-100"
          >
            Заменить
          </button>
          <button
            @click="form.coverUrl = ''"
            class="px-3 py-1.5 text-sm font-medium bg-white text-red-600 rounded-lg hover:bg-red-50"
          >
            Удалить
          </button>
        </div>
      </div>
      <button
        v-else
        @click="coverInput?.click()"
        :disabled="coverUploading"
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
        <select
          v-model="form.categoryName"
          class="px-3 py-2 rounded-lg border border-gray-200 text-sm text-gray-700 outline-none
                 focus:border-blue-400 focus:ring-2 focus:ring-blue-100 bg-white"
        >
          <option value="">— выберите —</option>
          <option v-for="cat in categories" :key="cat.id" :value="cat.name">{{ cat.name }}</option>
        </select>
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium text-gray-500">Краткое описание</label>
        <input
          v-model="form.description"
          type="text"
          placeholder="Несколько предложений о статье"
          class="px-3 py-2 rounded-lg border border-gray-200 text-sm text-gray-700 outline-none
                 focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
        />
      </div>
    </div>

    <!-- Editor card -->
    <div class="border border-gray-200 rounded-xl">

      <!-- ── Toolbar row 1: text formatting ── -->
      <div class="flex flex-wrap items-center gap-0.5 px-2 py-1.5 bg-gray-50 border-b border-gray-100 rounded-t-xl">

        <button @click="editor?.chain().focus().toggleBold().run()"
                :class="['toolbar-btn', btnCls('bold')]" title="Жирный">
          <strong class="text-sm leading-none">B</strong>
        </button>
        <button @click="editor?.chain().focus().toggleItalic().run()"
                :class="['toolbar-btn', btnCls('italic')]" title="Курсив">
          <em class="text-sm leading-none">I</em>
        </button>
        <button @click="editor?.chain().focus().toggleUnderline().run()"
                :class="['toolbar-btn', btnCls('underline')]" title="Подчёркнутый">
          <span class="text-sm underline leading-none">U</span>
        </button>
        <button @click="editor?.chain().focus().toggleStrike().run()"
                :class="['toolbar-btn', btnCls('strike')]" title="Зачёркнутый">
          <span class="text-sm line-through leading-none">S</span>
        </button>

        <div class="w-px h-5 bg-gray-200 mx-1" />

        <button @click="editor?.chain().focus().toggleHeading({ level: 1 }).run()"
                :class="['toolbar-btn text-xs font-bold', btnCls('heading', { level: 1 })]">H1</button>
        <button @click="editor?.chain().focus().toggleHeading({ level: 2 }).run()"
                :class="['toolbar-btn text-xs font-bold', btnCls('heading', { level: 2 })]">H2</button>
        <button @click="editor?.chain().focus().toggleHeading({ level: 3 }).run()"
                :class="['toolbar-btn text-xs font-bold', btnCls('heading', { level: 3 })]">H3</button>

        <div class="w-px h-5 bg-gray-200 mx-1" />

        <button @click="editor?.chain().focus().toggleBulletList().run()"
                :class="['toolbar-btn', btnCls('bulletList')]" title="Маркированный список">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>
          </svg>
        </button>
        <button @click="editor?.chain().focus().toggleOrderedList().run()"
                :class="['toolbar-btn', btnCls('orderedList')]" title="Нумерованный список">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M7 8h10M7 12h10M7 16h10M3 8h.01M3 12h.01M3 16h.01"/>
          </svg>
        </button>
        <button @click="editor?.chain().focus().toggleBlockquote().run()"
                :class="['toolbar-btn', btnCls('blockquote')]" title="Цитата">
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
            <path d="M10 7H6C4.9 7 4 7.9 4 9v4c0 1.1.9 2 2 2h2l-2 4h2l2-4V9c0-1.1-.9-2-2-2zm8 0h-4c-1.1 0-2 .9-2 2v4c0 1.1.9 2 2 2h2l-2 4h2l2-4V9c0-1.1-.9-2-2-2z"/>
          </svg>
        </button>
        <button @click="editor?.chain().focus().toggleCodeBlock().run()"
                :class="['toolbar-btn', btnCls('codeBlock')]" title="Блок кода">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/>
          </svg>
        </button>

        <div class="w-px h-5 bg-gray-200 mx-1" />

        <!-- Link dialog -->
        <div class="relative">
          <button @click="openLinkDialog"
                  :class="['toolbar-btn', btnCls('link')]" title="Ссылка">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/>
            </svg>
          </button>
          <div
            v-if="showLinkDialog"
            class="absolute top-10 left-0 z-30 bg-white border border-gray-200 rounded-xl shadow-xl p-3 w-72"
          >
            <p class="text-xs font-medium text-gray-500 mb-2">Вставить ссылку</p>
            <div class="flex gap-2">
              <input
                ref="linkInputRef"
                v-model="linkHref"
                type="text"
                placeholder="https://example.com"
                class="flex-1 px-2 py-1.5 text-sm border border-gray-200 rounded-lg outline-none focus:border-blue-400"
                @keydown.enter.prevent="applyLink"
                @keydown.escape="cancelLink"
              />
              <button
                @click="applyLink"
                class="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >ОК</button>
            </div>
            <div class="flex gap-3 mt-1.5">
              <button @click="cancelLink" class="text-xs text-gray-400 hover:text-gray-600">Отмена</button>
              <button
                v-if="editor?.isActive('link')"
                @click="editor?.chain().focus().unsetLink().run(); showLinkDialog = false"
                class="text-xs text-red-400 hover:text-red-600"
              >Удалить ссылку</button>
            </div>
          </div>
        </div>

        <!-- Image upload -->
        <button
          @click="imageInput?.click()"
          :disabled="imageUploading"
          class="toolbar-btn text-gray-600 hover:bg-gray-100"
          title="Вставить изображение"
        >
          <div v-if="imageUploading" class="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
          <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
          </svg>
        </button>

        <div class="w-px h-5 bg-gray-200 mx-1" />

        <!-- Undo / Redo -->
        <button @click="editor?.chain().focus().undo().run()"
                class="toolbar-btn text-gray-600 hover:bg-gray-100" title="Отменить">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 010 16H3m0-16l4-4M3 10l4 4"/>
          </svg>
        </button>
        <button @click="editor?.chain().focus().redo().run()"
                class="toolbar-btn text-gray-600 hover:bg-gray-100" title="Повторить">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 10H11a8 8 0 000 16h10m0-16l-4-4m4 4l-4 4"/>
          </svg>
        </button>

        <div class="w-px h-5 bg-gray-200 mx-1" />

        <!-- Text alignment -->
        <button @click="editor?.chain().focus().setTextAlign('left').run()"
                :class="['toolbar-btn', btnCls('textAlign', { textAlign: 'left' })]" title="По левому краю">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h10M4 14h16M4 18h10"/>
          </svg>
        </button>
        <button @click="editor?.chain().focus().setTextAlign('center').run()"
                :class="['toolbar-btn', btnCls('textAlign', { textAlign: 'center' })]" title="По центру">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M7 10h10M4 14h16M7 18h10"/>
          </svg>
        </button>
        <button @click="editor?.chain().focus().setTextAlign('right').run()"
                :class="['toolbar-btn', btnCls('textAlign', { textAlign: 'right' })]" title="По правому краю">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M10 10h10M4 14h16M10 18h10"/>
          </svg>
        </button>
        <button @click="editor?.chain().focus().setTextAlign('justify').run()"
                :class="['toolbar-btn', btnCls('textAlign', { textAlign: 'justify' })]" title="По ширине">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"/>
          </svg>
        </button>
      </div>

      <!-- ── Toolbar row 2: fonts + table ── -->
      <div class="flex flex-wrap items-center gap-2 px-3 py-1.5 bg-gray-50 border-b border-gray-200">

        <!-- Font family -->
        <select
          v-model="selectedFontFamily"
          @change="applyFontFamily(selectedFontFamily)"
          class="text-xs px-2 py-1 border border-gray-200 rounded-md bg-white text-gray-600
                 outline-none focus:border-blue-400 cursor-pointer"
        >
          <option v-for="f in fontFamilies" :key="f.value" :value="f.value">{{ f.label }}</option>
        </select>

        <!-- Font size -->
        <select
          v-model="selectedFontSize"
          @change="applyFontSize(selectedFontSize)"
          class="text-xs px-2 py-1 border border-gray-200 rounded-md bg-white text-gray-600
                 outline-none focus:border-blue-400 cursor-pointer"
        >
          <option value="">Размер</option>
          <option v-for="s in fontSizes" :key="s.value" :value="s.value">{{ s.label }}</option>
        </select>

        <div class="w-px h-5 bg-gray-200" />

        <!-- Insert table -->
        <button
          @click="editor?.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()"
          class="toolbar-btn text-gray-600 hover:bg-gray-100 flex items-center gap-1 text-xs px-2"
          title="Вставить таблицу"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M3 10h18M3 14h18M10 3v18M6 3h12a1 1 0 011 1v16a1 1 0 01-1 1H6a1 1 0 01-1-1V4a1 1 0 011-1z"/>
          </svg>
          Таблица
        </button>

        <!-- Table controls (visible when cursor is in table) -->
        <template v-if="editor?.isActive('table')">
          <div class="w-px h-5 bg-gray-200" />
          <button
            @click="editor?.chain().focus().addColumnBefore().run()"
            class="toolbar-btn text-xs text-gray-600 hover:bg-gray-100 px-2"
            title="Добавить столбец слева"
          >+ столб</button>
          <button
            @click="editor?.chain().focus().addRowBefore().run()"
            class="toolbar-btn text-xs text-gray-600 hover:bg-gray-100 px-2"
            title="Добавить строку выше"
          >+ строка</button>
          <button
            @click="editor?.chain().focus().deleteColumn().run()"
            class="toolbar-btn text-xs text-red-400 hover:bg-red-50 px-2"
          >- столб</button>
          <button
            @click="editor?.chain().focus().deleteRow().run()"
            class="toolbar-btn text-xs text-red-400 hover:bg-red-50 px-2"
          >- строка</button>
        </template>
      </div>

      <!-- ── Content area: scrollable ── -->
      <div class="overflow-y-auto rounded-b-xl" style="height: 460px;">
        <EditorContent :editor="editor" class="editor-content h-full" />
      </div>

    </div>

    <!-- Error -->
    <p v-if="saveError" class="mt-3 text-sm text-red-500 bg-red-50 px-3 py-2 rounded-lg">
      {{ saveError }}
    </p>

    <!-- Action buttons -->
    <div class="flex justify-end gap-3 mt-6">
      <button
        @click="save(true)"
        :disabled="saving"
        class="px-5 py-2.5 text-sm font-medium border border-gray-300 rounded-lg text-gray-700
               hover:border-blue-400 hover:text-blue-600 disabled:opacity-50 transition-colors"
      >
        {{ saving ? 'Сохранение...' : 'Сохранить черновик' }}
      </button>
      <button
        @click="save(false)"
        :disabled="saving"
        class="px-5 py-2.5 text-sm font-medium bg-blue-600 text-white rounded-lg
               hover:bg-blue-700 disabled:opacity-60 transition-colors"
      >
        {{ saving ? 'Публикация...' : 'Опубликовать' }}
      </button>
    </div>

  </div>
</template>

<style scoped>
.toolbar-btn {
  @apply p-1.5 rounded-md transition-colors flex items-center justify-center min-w-[2rem] h-8 flex-shrink-0;
}

/* ProseMirror base */
:deep(.ProseMirror) {
  @apply outline-none px-5 py-4;
  min-height: 100%;
  caret-color: #3b82f6;
  line-height: 1.75;
  font-size: 1rem;
}

:deep(.ProseMirror > * + *) { margin-top: 0.6em; }

/* Headings */
:deep(.ProseMirror h1) { @apply text-3xl font-bold text-gray-900 mt-4 mb-1; }
:deep(.ProseMirror h2) { @apply text-2xl font-bold text-gray-900 mt-3 mb-1; }
:deep(.ProseMirror h3) { @apply text-xl font-semibold text-gray-900 mt-2 mb-1; }

:deep(.ProseMirror p) { @apply text-gray-700; }

/* Lists */
:deep(.ProseMirror ul) { @apply list-disc pl-6 space-y-1; }
:deep(.ProseMirror ol) { @apply list-decimal pl-6 space-y-1; }

/* Blockquote */
:deep(.ProseMirror blockquote) {
  @apply border-l-4 border-blue-200 pl-4 text-gray-500 italic my-3;
}

/* Code block (IDE-like) */
:deep(.ProseMirror pre) {
  background: #282c34;
  color: #abb2bf;
  border-radius: 0.5rem;
  padding: 1rem 1.25rem;
  overflow-x: auto;
  margin: 0.75rem 0;
  font-family: 'Fira Code', 'Consolas', 'Monaco', monospace;
  font-size: 0.875rem;
  line-height: 1.6;
}
:deep(.ProseMirror pre code) {
  color: inherit;
  background: transparent;
  padding: 0;
  border-radius: 0;
  font-size: inherit;
}

/* Inline code */
:deep(.ProseMirror code) {
  @apply bg-gray-100 text-red-500 px-1.5 py-0.5 rounded text-sm font-mono;
}

/* Images */
:deep(.ProseMirror img) {
  @apply max-w-full h-auto rounded-lg my-3;
}

/* Links */
:deep(.ProseMirror a) {
  @apply text-blue-600 underline cursor-pointer;
}

/* Tables */
:deep(.ProseMirror table) {
  border-collapse: collapse;
  width: 100%;
  margin: 0.75rem 0;
  font-size: 0.9rem;
}
:deep(.ProseMirror th) {
  @apply bg-gray-50 font-semibold text-gray-700;
  border: 1px solid #e5e7eb;
  padding: 0.5rem 0.75rem;
  text-align: left;
}
:deep(.ProseMirror td) {
  border: 1px solid #e5e7eb;
  padding: 0.5rem 0.75rem;
  vertical-align: top;
}
:deep(.ProseMirror .selectedCell) {
  @apply bg-blue-50;
}

/* Placeholder */
:deep(.ProseMirror p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder);
  @apply text-gray-300;
  float: left;
  height: 0;
  pointer-events: none;
}
</style>
