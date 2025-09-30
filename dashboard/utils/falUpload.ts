// FAL Upload Utility
// This will handle image uploads using the FAL SDK

export interface UploadResult {
  url: string
  file_name: string
  file_size: number
  content_type: string
}

export async function uploadImageToFal(file: File): Promise<UploadResult> {
  try {
    // For now, convert to base64 data URL as fallback
    // TODO: Integrate with actual FAL upload when FAL_API_KEY is available
    
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      
      reader.onload = (e) => {
        const result = e.target?.result as string
        resolve({
          url: result, // Base64 data URL
          file_name: file.name,
          file_size: file.size,
          content_type: file.type
        })
      }
      
      reader.onerror = () => {
        reject(new Error('Failed to read file'))
      }
      
      reader.readAsDataURL(file)
    })
    
    /* 
    // Future implementation with actual FAL SDK:
    
    import * as fal from '@fal-ai/serverless-client'
    
    fal.config({
      credentials: process.env.NEXT_PUBLIC_FAL_API_KEY
    })
    
    const uploadedFile = await fal.upload(file)
    
    return {
      url: uploadedFile.url,
      file_name: file.name,
      file_size: file.size,
      content_type: file.type
    }
    */
    
  } catch (error) {
    console.error('Upload failed:', error)
    throw new Error(`Failed to upload image: ${error}`)
  }
}

export function validateImageFile(file: File): { valid: boolean; error?: string } {
  // Check file type
  if (!file.type.startsWith('image/')) {
    return { valid: false, error: 'Please select an image file' }
  }
  
  // Check file size (max 10MB)
  if (file.size > 10 * 1024 * 1024) {
    return { valid: false, error: 'Image must be smaller than 10MB' }
  }
  
  // Check image dimensions would require loading the image
  // For now, just validate type and size
  
  return { valid: true }
}

export function getOptimalImageDimensions(originalWidth: number, originalHeight: number): { width: number; height: number } {
  // LTX model works best with specific resolutions
  const supportedResolutions = [
    { width: 640, height: 480 },   // 4:3
    { width: 854, height: 480 },   // 16:9 SD
    { width: 1024, height: 576 },  // 16:9 HD
    { width: 512, height: 512 },   // 1:1
  ]
  
  const aspectRatio = originalWidth / originalHeight
  
  // Find the best matching resolution
  let bestMatch = supportedResolutions[0]
  let bestScore = Infinity
  
  for (const resolution of supportedResolutions) {
    const resolutionAspectRatio = resolution.width / resolution.height
    const aspectDifference = Math.abs(aspectRatio - resolutionAspectRatio)
    
    if (aspectDifference < bestScore) {
      bestScore = aspectDifference
      bestMatch = resolution
    }
  }
  
  return bestMatch
}
