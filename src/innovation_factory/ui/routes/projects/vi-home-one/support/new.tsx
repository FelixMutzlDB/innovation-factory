import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { Suspense, useState, useCallback } from 'react'
import { ErrorBoundary } from 'react-error-boundary'
import { useDropzone } from 'react-dropzone'
import { useQueryClient } from '@tanstack/react-query'
import {
  Upload,
  X,
  FileImage,
  FileVideo,
  FileText,
  Loader2,
} from 'lucide-react'
import {
  useVh_get_neighborhood_summarySuspense,
  useVh_create_ticket,
  vh_list_ticketsKey,
} from '@/lib/api'
import selector from '@/lib/selector'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

export const Route = createFileRoute('/projects/vi-home-one/support/new')({
  component: NewTicketPage,
})

function NewTicketPage() {
  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-3xl font-bold">Create Support Ticket</h1>
        <p className="text-muted-foreground">
          Describe your issue and upload relevant media
        </p>
      </div>

      <ErrorBoundary
        fallbackRender={({ error, resetErrorBoundary }) => (
          <Card className="p-6">
            <div className="text-center">
              <p className="text-destructive mb-4">Error: {error.message}</p>
              <Button onClick={resetErrorBoundary}>Try Again</Button>
            </div>
          </Card>
        )}
      >
        <Suspense fallback={<FormSkeleton />}>
          <TicketForm />
        </Suspense>
      </ErrorBoundary>
    </div>
  )
}

function TicketForm() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data: summary } = useVh_get_neighborhood_summarySuspense({
    params: { neighborhood_id: 1 },
    ...selector()
  })
  const createTicket = useVh_create_ticket()

  const [formData, setFormData] = useState({
    subject: '',
    description: '',
    deviceType: '',
    householdId: summary.households[0]?.id || 1,
  })
  const [files, setFiles] = useState<File[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setFiles((prev) => [...prev, ...acceptedFiles])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif'],
      'video/*': ['.mp4', '.mov', '.avi'],
      'audio/*': ['.mp3', '.wav', '.m4a'],
      'text/*': ['.txt', '.log'],
    },
    maxSize: 50 * 1024 * 1024, // 50MB
  })

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.subject || !formData.description) {
      return
    }

    setIsSubmitting(true)
    try {
      const ticket = await createTicket.mutateAsync({
        params: { household_id: formData.householdId },
        data: {
          title: formData.subject,
          description: formData.description,
          device_id: undefined, // Could be added later when device selection is implemented
        },
      })

      // Invalidate tickets list to refresh data
      queryClient.invalidateQueries({ queryKey: vh_list_ticketsKey({ household_id: formData.householdId }) })

      // In a real app, would upload files here
      // for (const file of files) {
      //   await uploadTicketMedia.mutateAsync({
      //     ticketId: ticket.id,
      //     data: { file }
      //   })
      // }

      navigate({ to: '/projects/vi-home-one/support/$ticketId', params: { ticketId: ticket.data.id.toString() } })
    } catch (error) {
      console.error('Failed to create ticket:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) return <FileImage className="h-5 w-5" />
    if (file.type.startsWith('video/')) return <FileVideo className="h-5 w-5" />
    return <FileText className="h-5 w-5" />
  }

  return (
    <form onSubmit={handleSubmit}>
      <Card className="p-6">
        <div className="space-y-6">
          {/* Household Selection */}
          <div className="space-y-2">
            <Label htmlFor="household">Household</Label>
            <Select
              value={formData.householdId.toString()}
              onValueChange={(value) =>
                setFormData({ ...formData, householdId: parseInt(value) })
              }
            >
              <SelectTrigger id="household">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {summary.households.map((household) => (
                  <SelectItem key={household.id} value={household.id.toString()}>
                    {household.owner_name} - {household.address}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Device Type */}
          <div className="space-y-2">
            <Label htmlFor="device">Device Type (Optional)</Label>
            <Select
              value={formData.deviceType}
              onValueChange={(value) =>
                setFormData({ ...formData, deviceType: value })
              }
            >
              <SelectTrigger id="device">
                <SelectValue placeholder="Select device type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="heat_pump">Heat Pump</SelectItem>
                <SelectItem value="pv_panel">Solar Panel</SelectItem>
                <SelectItem value="battery">Battery Storage</SelectItem>
                <SelectItem value="ev_charger">EV Charger</SelectItem>
                <SelectItem value="grid_meter">Grid Meter</SelectItem>
                <SelectItem value="other">Other</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Subject */}
          <div className="space-y-2">
            <Label htmlFor="subject">Subject *</Label>
            <Input
              id="subject"
              placeholder="Brief description of the issue"
              value={formData.subject}
              onChange={(e) =>
                setFormData({ ...formData, subject: e.target.value })
              }
              required
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description *</Label>
            <textarea
              id="description"
              placeholder="Detailed description of the issue..."
              className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
              required
            />
          </div>

          {/* File Upload */}
          <div className="space-y-2">
            <Label>Media Files (Optional)</Label>
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                isDragActive
                  ? 'border-primary bg-primary/5'
                  : 'border-muted-foreground/25 hover:border-primary/50'
              }`}
            >
              <input {...getInputProps()} />
              <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
              {isDragActive ? (
                <p className="text-sm text-muted-foreground">Drop files here...</p>
              ) : (
                <>
                  <p className="text-sm font-medium mb-1">
                    Drag & drop files here, or click to select
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Images, videos, audio, or text files (max 50MB)
                  </p>
                </>
              )}
            </div>

            {/* File List */}
            {files.length > 0 && (
              <div className="space-y-2 mt-4">
                {files.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-3 p-3 rounded-lg border"
                  >
                    <div className="text-primary">{getFileIcon(file)}</div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{file.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removeFile(index)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <Button
              type="submit"
              disabled={isSubmitting || !formData.subject || !formData.description}
              className="gap-2"
            >
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              Create Ticket
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate({ to: '/projects/vi-home-one/support' })}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
          </div>
        </div>
      </Card>
    </form>
  )
}

function FormSkeleton() {
  return (
    <Card className="p-6">
      <div className="space-y-6">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-12" />
        ))}
        <Skeleton className="h-32" />
      </div>
    </Card>
  )
}
