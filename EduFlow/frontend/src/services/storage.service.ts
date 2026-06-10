import imageCompression from 'browser-image-compression'
import { supabase } from './supabase'

const BUCKET = 'Article'
const COMPRESSIBLE_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif']

export async function uploadImage(file: File): Promise<string> {
  let uploadFile: File = file
  const isCompressible = COMPRESSIBLE_TYPES.includes(file.type)

  if (isCompressible) {
    try {
      uploadFile = await imageCompression(file, {
        maxSizeMB: 0.5,
        maxWidthOrHeight: 1920,
        useWebWorker: true,
        fileType: 'image/webp',
        initialQuality: 0.85
      })
    } catch {
      // compression failed — upload original
    }
  }

  const ext = isCompressible ? 'webp' : (file.name.split('.').pop() ?? 'bin')
  const path = `${Date.now()}-${Math.random().toString(36).slice(2)}.${ext}`
  const contentType = isCompressible ? 'image/webp' : file.type

  const { data, error } = await supabase.storage
    .from(BUCKET)
    .upload(path, uploadFile, { contentType, upsert: false })

  if (error) {
    throw new Error(`Supabase: ${error.message}`)
  }

  return supabase.storage.from(BUCKET).getPublicUrl(data.path).data.publicUrl
}
