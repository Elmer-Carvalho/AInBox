"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent } from "@/components/ui/card"
import {
  Upload,
  X,
  FileText,
  File,
  Plus,
  Loader2,
  Mail,
  Bot,
  AlertCircle,
  Copy,
  Info,
  Trash2,
  Check,
  ChevronUp,
  ChevronDown,
  Github,
  Linkedin,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"

interface UploadedFile {
  id: string
  name: string
  type: string
  size: number
  file: File
}

interface Message {
  id: string
  text: string
}

interface ContextFile {
  id: string
  name: string
  type: string
  size: number
  file: File
}

interface FeedbackItem {
  id: string
  type: "productive" | "unproductive"
  originalContent: string
  suggestion?: string
  preview: string
  emailIndex: number
}

interface ErrorModalProps {
  isOpen: boolean
  onClose: () => void
  message: string
}

function ErrorModal({ isOpen, onClose, message }: ErrorModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-slate-800 border-slate-700 text-slate-100 max-w-md animate-in fade-in-0 zoom-in-95 duration-300">
        <DialogHeader>
          <DialogTitle className="text-red-400 flex items-center space-x-2">
            <AlertCircle className="h-5 w-5" />
            <span>Erro</span>
          </DialogTitle>
        </DialogHeader>
        <div className="mt-4">
          <p className="text-slate-200 leading-relaxed">{message}</p>
        </div>
      </DialogContent>
    </Dialog>
  )
}

interface InfoModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  content: string
}

function InfoModal({ isOpen, onClose, title, content }: InfoModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-slate-800 border-slate-700 text-slate-100 max-w-md animate-in fade-in-0 zoom-in-95 duration-300">
        <DialogHeader>
          <DialogTitle className="text-cyan-300">{title}</DialogTitle>
        </DialogHeader>
        <div className="mt-4">
          <p className="text-slate-200 leading-relaxed text-justify">{content}</p>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export function AInBoxInterface() {
  const [currentMessage, setCurrentMessage] = useState("")
  const [messages, setMessages] = useState<Message[]>([])
  const [context, setContext] = useState("")
  const [contextFile, setContextFile] = useState<ContextFile | null>(null)
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [isDragOver, setIsDragOver] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [feedbackItems, setFeedbackItems] = useState<FeedbackItem[]>([])
  const [selectedFeedback, setSelectedFeedback] = useState<FeedbackItem | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [errorModal, setErrorModal] = useState({ isOpen: false, message: "" })
  const [websocket, setWebsocket] = useState<WebSocket | null>(null)
  const [connectionId, setConnectionId] = useState<string | null>(null)
  const [isAnimating, setIsAnimating] = useState(false)
  const [infoModal, setInfoModal] = useState({ isOpen: false, title: "", content: "" })
  const [isCopied, setIsCopied] = useState(false)
  const [isCopyAnimating, setIsCopyAnimating] = useState(false)
  const [expandedEmails, setExpandedEmails] = useState<Set<string>>(new Set())
  const [expandedOriginalContent, setExpandedOriginalContent] = useState(false)
  const [expandedReplyContent, setExpandedReplyContent] = useState(false)
  const [showOriginalSeeMore, setShowOriginalSeeMore] = useState(false)
  const [showReplySeeMore, setShowReplySeeMore] = useState(false)
  const originalContentRef = useRef<HTMLParagraphElement>(null)
  const replyContentRef = useRef<HTMLParagraphElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const contextFileInputRef = useRef<HTMLInputElement>(null)

  const MAX_EMAIL_CHARS = 15000
  const MAX_CONTEXT_CHARS = 15000

  const addMessage = () => {
    if (!currentMessage.trim() || messages.length >= 20 || currentMessage.length > MAX_EMAIL_CHARS) return

    const newMessage: Message = {
      id: Math.random().toString(36).substr(2, 9),
      text: currentMessage.trim(),
    }

    setMessages((prev) => [...prev, newMessage])
    setCurrentMessage("")
  }

  const removeMessage = (id: string) => {
    setMessages((prev) => prev.filter((msg) => msg.id !== id))
  }

  const handleFileUpload = (selectedFiles: FileList | null) => {
    if (!selectedFiles) return

    const validFiles = Array.from(selectedFiles).filter((file) => {
      const isValidType = file.type === "application/pdf" || file.type === "text/plain"
      const isValidExtension = file.name.endsWith(".pdf") || file.name.endsWith(".txt")
      const isValidSize = file.size <= 2 * 1024 * 1024 // 2MB limit

      if (!isValidSize) {
        setErrorModal({ isOpen: true, message: `Arquivo ${file.name} excede o limite de 2MB` })
        return false
      }

      return isValidType || isValidExtension
    })

    if (files.length + validFiles.length > 20) {
      setErrorModal({ isOpen: true, message: "Máximo de 20 arquivos permitidos" })
      return
    }

    const newFiles: UploadedFile[] = validFiles.map((file) => ({
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      type: file.type || (file.name.endsWith(".pdf") ? "application/pdf" : "text/plain"),
      size: file.size,
      file: file,
    }))

    setFiles((prev) => [...prev, ...newFiles])
  }

  const handleContextFileUpload = (selectedFiles: FileList | null) => {
    if (!selectedFiles || selectedFiles.length === 0) return

    const file = selectedFiles[0]
    const isValidType = file.type === "application/pdf" || file.type === "text/plain"
    const isValidExtension = file.name.endsWith(".pdf") || file.name.endsWith(".txt")
    const isValidSize = file.size <= 2 * 1024 * 1024 // 2MB limit

    if (!isValidSize) {
      setErrorModal({ isOpen: true, message: `Arquivo ${file.name} excede o limite de 2MB` })
      return
    }

    if (!isValidType && !isValidExtension) {
      setErrorModal({ isOpen: true, message: "Apenas arquivos .pdf e .txt são permitidos" })
      return
    }

    const newContextFile: ContextFile = {
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      type: file.type || (file.name.endsWith(".pdf") ? "application/pdf" : "text/plain"),
      size: file.size,
      file: file,
    }

    setContextFile(newContextFile)
  }

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((file) => file.id !== id))
  }

  const removeContextFile = () => {
    setContextFile(null)
  }

  const connectWebSocket = (): Promise<string> => {
    return new Promise((resolve, reject) => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "https://ainbox-backend-356969755759.southamerica-east1.run.app";
        const wsUrl = apiUrl.replace(/^http/, 'ws');
        const ws = new WebSocket(`${wsUrl}/ws`)

        ws.onopen = () => {
          console.log("[v0] WebSocket connected")
          setWebsocket(ws)
        }

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            console.log("[v0] WebSocket message received:", data)

            switch (data.type) {
              case "connection_established":
                setConnectionId(data.connection_id)
                resolve(data.connection_id)
                break

              case "analysis_result":
                const newFeedback: FeedbackItem = {
                  id: Math.random().toString(36).substr(2, 9),
                  type: data.data.classification.toLowerCase() === "produtivo" ? "productive" : "unproductive",
                  originalContent:
                    data.data.original_content || data.data["original-content"] || "Conteúdo original não disponível",
                  suggestion: data.data.suggestion,
                  preview:
                    (data.data.original_content || data.data["original-content"] || "Sem conteúdo").substring(0, 50) +
                    "...",
                  emailIndex: data.data.email_index,
                }
                setFeedbackItems((prev) => [newFeedback, ...prev])
                break

              case "analysis_complete":
                setIsLoading(false)
                setIsAnimating(false)
                console.log("[v0] Analysis complete:", data.message)
                break

              case "error":
                setErrorModal({ isOpen: true, message: data.message })
                setIsLoading(false)
                setIsAnimating(false)
                break

              case "ping":
                break
            }
          } catch (error) {
            console.error("[v0] Error parsing WebSocket message:", error)
          }
        }

        ws.onerror = (error) => {
          console.error("[v0] WebSocket error:", error)
          setErrorModal({ isOpen: true, message: "Erro de conexão com o servidor" })
          reject(error)
        }

        ws.onclose = () => {
          console.log("[v0] WebSocket disconnected")
          setWebsocket(null)
          setConnectionId(null)
        }
      } catch (error) {
        console.error("[v0] Error connecting to WebSocket:", error)
        setErrorModal({ isOpen: true, message: "Não foi possível conectar ao servidor" })
        reject(error)
      }
    })
  }

  const handleSend = async () => {
    const hasMessages = messages.length > 0
    const hasFiles = files.length > 0

    if (!hasMessages && !hasFiles) {
      setErrorModal({
        isOpen: true,
        message: "Por favor, adicione pelo menos um texto de email ou faça upload de arquivos",
      })
      return
    }

    setIsLoading(true)
    setIsAnimating(true)

    try {
      const connectionId = await connectWebSocket()

      const formData = new FormData()
      formData.append("connection_id", connectionId)

      if (hasMessages) {
        const emailStrings = messages.map((msg) => msg.text).join("\n\n")
        formData.append("email_strings", emailStrings)
      }

      files.forEach((file) => {
        formData.append("email_files", file.file)
      })

      if (context.trim()) {
        formData.append("context_string", context.trim())
      }

      if (contextFile) {
        formData.append("context_file", contextFile.file)
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "https://ainbox-backend-356969755759.southamerica-east1.run.app";
      const response = await fetch(`${apiUrl}/api/v1/analysis`, {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      setMessages([])
      setFiles([])
      setContext("")
      setContextFile(null)

      console.log("[v0] Request sent successfully")
    } catch (error) {
      console.error("[v0] Error sending request:", error)
      setErrorModal({ isOpen: true, message: `Erro ao enviar solicitação: ${error.message}` })
      setIsLoading(false)
      setIsAnimating(false)
      if (websocket) {
        websocket.close()
      }
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  const openFeedbackModal = (feedback: FeedbackItem) => {
    setSelectedFeedback(feedback)
    setIsModalOpen(true)
  }

  const openInfoModal = (title: string, content: string) => {
    setInfoModal({ isOpen: true, title, content })
  }

  const copyToClipboard = (text: string) => {
    setIsCopied(true)
    navigator.clipboard.writeText(text).then(() => {
      setTimeout(() => setIsCopied(false), 2000)
    })
  }

  const toggleEmailExpansion = (id: string) => {
    setExpandedEmails((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(id)) {
        newSet.delete(id)
      } else {
        newSet.add(id)
      }
      return newSet
    })
  }

  const clearAllResponses = () => {
    setFeedbackItems([])
  }

  const checkTextOverflow = (element: HTMLElement | null): boolean => {
    if (!element) return false
    return element.scrollHeight > element.clientHeight
  }

  useEffect(() => {
    if (isModalOpen && selectedFeedback) {
      setTimeout(() => {
        console.log("[v0] Checking text overflow for original content")
        console.log("[v0] Original content ref:", originalContentRef.current)
        if (originalContentRef.current) {
          console.log("[v0] ScrollHeight:", originalContentRef.current.scrollHeight)
          console.log("[v0] ClientHeight:", originalContentRef.current.clientHeight)
        }

        const originalOverflow = checkTextOverflow(originalContentRef.current)
        const replyOverflow = checkTextOverflow(replyContentRef.current)

        console.log("[v0] Original content overflow:", originalOverflow)
        console.log("[v0] Reply content overflow:", replyOverflow)

        setShowOriginalSeeMore(originalOverflow)
        setShowReplySeeMore(replyOverflow)
      }, 100)
    }
  }, [isModalOpen, selectedFeedback, expandedOriginalContent, expandedReplyContent])

  return (
    <div className="min-h-screen relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
        <div className="absolute inset-0 opacity-30">
          <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 to-blue-500/10"></div>
          <div
            className="absolute inset-0"
            style={{
              backgroundImage: `radial-gradient(circle at 1px 1px, rgba(255,255,255,0.15) 1px, transparent 0)`,
              backgroundSize: "20px 20px",
            }}
          ></div>
        </div>
        <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent"></div>
      </div>

      <div className="relative z-10 p-4 md:p-8">
        <div className="mb-8 md:mb-12">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <h1 className="text-3xl md:text-4xl font-bold font-sans">
                <span className="bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">AI</span>
                <span className="text-white">nBox</span>
              </h1>
              <div className="text-sm text-white hidden sm:block flex items-center h-full">
                Automação de E-mails com IA
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <a
                href="https://github.com/Elmer-Carvalho/AInBox"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center w-12 h-12 bg-slate-800/50 backdrop-blur-sm border border-slate-600 rounded-xl hover:bg-slate-700/50 hover:border-slate-500 hover:scale-110 transition-all duration-300 cursor-pointer group"
              >
                <Github className="h-6 w-6 text-white group-hover:text-cyan-400 transition-colors duration-300" />
              </a>
              <a
                href="https://www.linkedin.com/in/elmer-carvalho-79b3bb264"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center w-12 h-12 bg-slate-800/50 backdrop-blur-sm border border-slate-600 rounded-xl hover:bg-slate-700/50 hover:border-slate-500 hover:scale-110 transition-all duration-300 cursor-pointer group"
              >
                <Linkedin className="h-6 w-6 text-white group-hover:text-blue-400 transition-colors duration-300" />
              </a>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-4xl mx-auto space-y-6">
          <Card className="border-slate-700 bg-slate-800/50 backdrop-blur-sm">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-cyan-300">E-mail</h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() =>
                    openInfoModal(
                      "Seção de E-mail",
                      "Nesta seção, você pode digitar até 20 e-mails ou fazer upload de até 20 arquivos de e-mail (.pdf ou .txt), totalizando até 40 e-mails. Além de classificar os e-mails como produtivos ou improdutivos, a IA gerará respostas apropriadas para e-mails classificados como Produtivos, utilizando o contexto adicional que você fornecer.",
                    )
                  }
                  className="text-slate-400 hover:text-cyan-400 hover:bg-slate-700/50 cursor-pointer p-2"
                >
                  <Info className="h-4 w-4" />
                </Button>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <label className="block text-sm font-medium text-slate-200">
                    Digite os E-mails ({messages.length}/20):
                  </label>
                </div>

                <div className="relative">
                  <Textarea
                    placeholder="Digite o texto do seu email aqui..."
                    value={currentMessage}
                    onChange={(e) => setCurrentMessage(e.target.value)}
                    maxLength={MAX_EMAIL_CHARS}
                    className="min-h-[100px] resize-none bg-slate-700/50 border-slate-600 text-slate-100 placeholder:text-slate-400 pr-12 pb-12"
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault()
                        addMessage()
                      }
                    }}
                  />
                  <Button
                    onClick={addMessage}
                    disabled={
                      !currentMessage.trim() || messages.length >= 20 || currentMessage.length > MAX_EMAIL_CHARS
                    }
                    className="absolute right-3 bottom-2 bg-cyan-600 hover:bg-cyan-700 hover:scale-110 disabled:hover:scale-100 text-white h-8 w-8 p-0 transition-all duration-200 cursor-pointer"
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                  <div className="absolute bottom-2 left-3 text-xs text-slate-400">
                    {currentMessage.length}/{MAX_EMAIL_CHARS}
                  </div>
                </div>

                {messages.length > 0 && (
                  <div className="space-y-2 max-h-60 overflow-y-auto custom-scrollbar">
                    {messages.map((message) => {
                      const isExpanded = expandedEmails.has(message.id)
                      const isLong = message.text.length > 200
                      const displayText = isLong && !isExpanded ? message.text.substring(0, 200) + "..." : message.text

                      return (
                        <div
                          key={message.id}
                          className="flex items-start justify-between p-3 rounded-lg border bg-slate-700/30 border-slate-600 animate-in slide-in-from-top-2 duration-300"
                        >
                          <div className="flex-1 pr-4">
                            <div className="text-sm text-slate-200 whitespace-pre-wrap leading-relaxed">
                              {displayText}
                            </div>
                            {isLong && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => toggleEmailExpansion(message.id)}
                                className="text-cyan-400 hover:text-cyan-300 p-0 h-auto mt-2 cursor-pointer"
                              >
                                {isExpanded ? "Ver menos" : "Ver mais"}
                              </Button>
                            )}
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeMessage(message.id)}
                            className="text-slate-400 hover:text-white hover:bg-red-600/20 hover:scale-110 h-8 px-2 transition-all duration-200 cursor-pointer"
                          >
                            <X className="h-3 w-3" />
                          </Button>
                        </div>
                      )
                    })}
                  </div>
                )}

                {/* File Upload Section */}
                <div>
                  <label className="block text-sm font-medium text-slate-200 mb-2">
                    Arquivos de E-mails ({files.length}/20):
                  </label>
                  <div
                    className={cn(
                      "border-2 border-dashed rounded-lg p-6 text-center transition-colors",
                      isDragOver ? "border-cyan-400 bg-cyan-400/5" : "border-slate-600 hover:border-cyan-500/50",
                    )}
                    onDragOver={(e) => {
                      e.preventDefault()
                      setIsDragOver(true)
                    }}
                    onDragLeave={(e) => {
                      e.preventDefault()
                      setIsDragOver(false)
                    }}
                    onDrop={(e) => {
                      e.preventDefault()
                      setIsDragOver(false)
                      handleFileUpload(e.dataTransfer.files)
                    }}
                  >
                    <Upload className="mx-auto h-8 w-8 text-slate-400 mb-2" />
                    <p className="text-sm text-slate-300 mb-2">
                      Arraste e solte arquivos aqui, ou{" "}
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        className="text-cyan-400 hover:text-cyan-300 font-medium cursor-pointer"
                      >
                        Browse
                      </button>
                    </p>
                    <p className="text-xs text-slate-400">Apenas arquivos .pdf e .txt (máx 20 arquivos)</p>
                    <input
                      ref={fileInputRef}
                      type="file"
                      multiple
                      accept=".pdf,.txt"
                      onChange={(e) => handleFileUpload(e.target.files)}
                      className="hidden"
                    />
                  </div>

                  {files.length > 0 && (
                    <div className="mt-4 space-y-2 max-h-40 overflow-y-auto custom-scrollbar">
                      {files.map((file) => (
                        <div
                          key={file.id}
                          className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg border border-slate-600 animate-in slide-in-from-top-2 duration-300"
                        >
                          <div className="flex items-center space-x-3">
                            {file.type === "application/pdf" ? (
                              <FileText className="h-5 w-5 text-red-400" />
                            ) : (
                              <File className="h-5 w-5 text-cyan-400" />
                            )}
                            <div>
                              <p className="text-sm font-medium text-slate-200">{file.name}</p>
                              <p className="text-xs text-slate-400">{formatFileSize(file.size)}</p>
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeFile(file.id)}
                            className="text-slate-400 hover:text-white hover:bg-red-600/20 hover:scale-110 transition-all duration-200 cursor-pointer"
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-700 bg-slate-800/50 backdrop-blur-sm">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-cyan-300">Contexto Opcional</h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() =>
                    openInfoModal(
                      "Seção de Contexto",
                      "O contexto é fundamental para obter melhores resultados da IA. Forneça informações relevantes sobre sua empresa, projeto, ou situação específica. Quanto mais contexto relevante você fornecer, mais precisas e personalizadas serão as análises e sugestões da IA.",
                    )
                  }
                  className="text-slate-400 hover:text-cyan-400 hover:bg-slate-700/50 cursor-pointer p-2"
                >
                  <Info className="h-4 w-4" />
                </Button>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <label htmlFor="context" className="block text-sm font-medium text-slate-200">
                    Digite o Contexto
                  </label>
                </div>
                <div className="relative">
                  <Textarea
                    id="context"
                    placeholder="Forneça contexto adicional para melhores resultados..."
                    value={context}
                    onChange={(e) => setContext(e.target.value)}
                    maxLength={MAX_CONTEXT_CHARS}
                    className="min-h-[80px] resize-none bg-slate-700/50 border-slate-600 text-slate-100 placeholder:text-slate-400 pr-12 pb-8"
                  />
                  <div className="absolute bottom-2 left-3 text-xs text-slate-400">
                    {context.length}/{MAX_CONTEXT_CHARS}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-200 mb-2">
                    Arquivo de Contexto ({contextFile ? 1 : 0}/1):
                  </label>
                  {!contextFile ? (
                    <div
                      className="border-2 border-dashed rounded-lg p-6 text-center transition-colors border-slate-600 hover:border-cyan-500/50"
                      onDragOver={(e) => {
                        e.preventDefault()
                      }}
                      onDrop={(e) => {
                        e.preventDefault()
                        handleContextFileUpload(e.dataTransfer.files)
                      }}
                    >
                      <Upload className="mx-auto h-8 w-8 text-slate-400 mb-2" />
                      <p className="text-sm text-slate-300 mb-2">
                        Arraste e solte arquivo aqui, ou{" "}
                        <button
                          type="button"
                          onClick={() => contextFileInputRef.current?.click()}
                          className="text-cyan-400 hover:text-cyan-300 font-medium cursor-pointer"
                        >
                          Browse
                        </button>
                      </p>
                      <p className="text-xs text-slate-400">Apenas arquivos .pdf e .txt</p>
                      <input
                        ref={contextFileInputRef}
                        type="file"
                        accept=".pdf,.txt"
                        onChange={(e) => handleContextFileUpload(e.target.files)}
                        className="hidden"
                      />
                    </div>
                  ) : (
                    <div className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg border border-slate-600 animate-in slide-in-from-top-2 duration-300">
                      <div className="flex items-center space-x-3">
                        {contextFile.type === "application/pdf" ? (
                          <FileText className="h-5 w-5 text-red-400" />
                        ) : (
                          <File className="h-5 w-5 text-cyan-400" />
                        )}
                        <div>
                          <p className="text-sm font-medium text-slate-200">{contextFile.name}</p>
                          <p className="text-xs text-slate-400">{formatFileSize(contextFile.size)}</p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={removeContextFile}
                        className="text-slate-400 hover:text-white hover:bg-red-600/20 hover:scale-110 transition-all duration-200 cursor-pointer"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-center relative">
            <div className="relative">
              {!isAnimating ? (
                <Button
                  onClick={handleSend}
                  size="lg"
                  disabled={messages.length === 0 && files.length === 0}
                  className="px-8 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 hover:scale-105 disabled:hover:scale-100 text-white font-medium shadow-lg transition-all duration-300 cursor-pointer"
                >
                  Enviar para Análise
                </Button>
              ) : (
                <div className="px-8 py-3 flex items-center justify-center space-x-1 relative">
                  {[...Array(3)].map((_, i) => (
                    <Mail
                      key={`envelope-${i}`}
                      className="absolute h-5 w-5 text-cyan-400"
                      style={{
                        left: `${30 + i * 15}%`,
                        animation: `flyEnvelope 2s ease-in-out infinite`,
                        animationDelay: `${i * 0.3}s`,
                      }}
                    />
                  ))}
                  {["E", "n", "v", "i", "a", "n", "d", "o"].map((letter, i) => (
                    <span
                      key={i}
                      className="text-cyan-400 font-medium text-lg"
                      style={{
                        animation: `flyLetter 2s ease-in-out infinite`,
                        animationDelay: `${i * 0.1}s`,
                      }}
                    >
                      {letter}
                    </span>
                  ))}
                  {[...Array(8)].map((_, i) => (
                    <div
                      key={`wind-${i}`}
                      className="absolute w-1 h-1 bg-cyan-400/60 rounded-full"
                      style={{
                        left: `${20 + i * 10}%`,
                        top: `${40 + (i % 3) * 15}%`,
                        animation: `windParticle 1.5s ease-out infinite`,
                        animationDelay: `${i * 0.2}s`,
                      }}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>

          {(isLoading || feedbackItems.length > 0) && (
            <Card className="border-slate-700 bg-slate-800/50 backdrop-blur-sm">
              <CardContent className="p-6">
                <div className="flex items-center justify-center mb-6 relative">
                  <div className="text-center">
                    <h3 className="text-xl font-bold text-cyan-300 mb-2">Resultados da Análise</h3>
                    <div className="w-24 h-1 bg-gradient-to-r from-cyan-400 to-blue-400 mx-auto rounded-full"></div>
                  </div>
                  {feedbackItems.length > 0 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={clearAllResponses}
                      className="absolute right-0 text-slate-400 hover:text-red-400 hover:bg-red-600/10 cursor-pointer flex items-center space-x-2"
                    >
                      <Trash2 className="h-4 w-4" />
                      <span>Limpar</span>
                    </Button>
                  )}
                </div>

                <div className="grid md:grid-cols-2 gap-8">
                  <div className="space-y-4">
                    <div className="flex items-center justify-center">
                      <div className="flex items-center space-x-3 bg-green-900/20 px-4 py-2 rounded-full border border-green-700/50">
                        <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                        <h4 className="text-sm font-medium text-green-400">E-mails Produtivos</h4>
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-3">
                      {feedbackItems
                        .filter((item) => item.type === "productive")
                        .map((item) => (
                          <button
                            key={item.id}
                            onClick={() => openFeedbackModal(item)}
                            className="aspect-square bg-green-900/20 border border-green-700/50 rounded-lg p-3 hover:bg-green-900/30 hover:scale-105 transition-all duration-200 group cursor-pointer"
                          >
                            <div className="text-xs text-green-300 transition-all duration-200 leading-tight">
                              {item.preview}
                            </div>
                          </button>
                        ))}
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-center justify-center">
                      <div className="flex items-center space-x-3 bg-red-900/20 px-4 py-2 rounded-full border border-red-700/50">
                        <div className="w-3 h-3 bg-red-400 rounded-full"></div>
                        <h4 className="text-sm font-medium text-red-400">E-mails Improdutivos</h4>
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-3">
                      {feedbackItems
                        .filter((item) => item.type === "unproductive")
                        .map((item) => (
                          <button
                            key={item.id}
                            onClick={() => openFeedbackModal(item)}
                            className="aspect-square bg-red-900/20 border border-red-700/50 rounded-lg p-3 hover:bg-red-900/30 hover:scale-105 transition-all duration-200 group cursor-pointer"
                          >
                            <div className="text-xs text-red-300 transition-all duration-200 leading-tight">
                              {item.preview}
                            </div>
                          </button>
                        ))}
                    </div>
                  </div>
                </div>

                {isLoading && (
                  <div className="mt-8 text-center">
                    <Loader2 className="mx-auto h-6 w-6 animate-spin text-cyan-400" />
                    <p className="text-sm text-slate-400 mt-2">Analisando emails...</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="bg-slate-800 border-slate-700 text-slate-100 max-w-4xl max-h-[80vh] overflow-y-auto custom-modal-scrollbar animate-in fade-in-0 zoom-in-95 duration-300">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-3 text-lg">
              <div
                className={cn(
                  "w-4 h-4 rounded-full",
                  selectedFeedback?.type === "productive" ? "bg-green-400" : "bg-red-400",
                )}
              ></div>
              <span className={selectedFeedback?.type === "productive" ? "text-green-400" : "text-red-400"}>
                {selectedFeedback?.type === "productive" ? "E-mail Produtivo" : "E-mail Improdutivo"}
              </span>
            </DialogTitle>
          </DialogHeader>

          <div className="mt-6 space-y-6">
            {/* Original Content Section */}
            <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-600">
              <h4 className="text-sm font-semibold text-slate-300 mb-3 flex items-center">
                <FileText className="h-4 w-4 mr-2" />
                Conteúdo Original
              </h4>
              <div>
                <p
                  ref={originalContentRef}
                  className={cn(
                    "text-slate-200 leading-relaxed whitespace-pre-wrap",
                    !expandedOriginalContent && "line-clamp-6 overflow-hidden",
                  )}
                >
                  {selectedFeedback?.originalContent || "Nenhum conteúdo original disponível."}
                </p>
                {showOriginalSeeMore && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setExpandedOriginalContent(!expandedOriginalContent)}
                    className="mt-3 text-cyan-400 hover:text-cyan-300 hover:bg-slate-700/50 transition-all duration-200 cursor-pointer flex items-center space-x-2"
                  >
                    {expandedOriginalContent ? (
                      <>
                        <ChevronUp className="h-4 w-4 mr-1" />
                        Ver menos
                      </>
                    ) : (
                      <>
                        <ChevronDown className="h-4 w-4 mr-1" />
                        Ver mais
                      </>
                    )}
                  </Button>
                )}
              </div>
            </div>

            {/* AI Suggestion Section (only for productive emails) */}
            {selectedFeedback?.type === "productive" && selectedFeedback?.suggestion && (
              <div className="bg-green-900/10 rounded-lg p-4 border border-green-700/30">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-semibold text-green-300 flex items-center">
                    <Bot className="h-4 w-4 mr-2" />
                    Resposta Sugerida pela IA
                  </h4>
                  <Button
                    size="sm"
                    onClick={() => copyToClipboard(selectedFeedback.suggestion!)}
                    className={cn(
                      "bg-green-600/20 hover:bg-green-600/30 text-green-300 border border-green-600/50 transition-all duration-200 cursor-pointer flex items-center space-x-2",
                      isCopied ? "scale-95" : "hover:scale-105",
                    )}
                  >
                    {isCopied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                    <span>{isCopied ? "Copiado!" : "Copiar"}</span>
                  </Button>
                </div>
                <div>
                  <p
                    ref={replyContentRef}
                    className={cn(
                      "text-slate-200 leading-relaxed whitespace-pre-wrap",
                      !expandedReplyContent && "line-clamp-6 overflow-hidden",
                    )}
                  >
                    {selectedFeedback.suggestion}
                  </p>
                  {showReplySeeMore && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setExpandedReplyContent(!expandedReplyContent)}
                      className="mt-3 text-cyan-400 hover:text-cyan-300 hover:bg-slate-700/50 transition-all duration-200 cursor-pointer flex items-center space-x-2"
                    >
                      {expandedReplyContent ? (
                        <>
                          <ChevronUp className="h-4 w-4 mr-1" />
                          Ver menos
                        </>
                      ) : (
                        <>
                          <ChevronDown className="h-4 w-4 mr-1" />
                          Ver mais
                        </>
                      )}
                    </Button>
                  )}
                </div>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      <InfoModal
        isOpen={infoModal.isOpen}
        onClose={() => setInfoModal({ isOpen: false, title: "", content: "" })}
        title={infoModal.title}
        content={infoModal.content}
      />

      <ErrorModal
        isOpen={errorModal.isOpen}
        onClose={() => setErrorModal({ isOpen: false, message: "" })}
        message={errorModal.message}
      />

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar,
        .custom-modal-scrollbar::-webkit-scrollbar {
          width: 6px;
        }

        .custom-scrollbar::-webkit-scrollbar-track,
        .custom-modal-scrollbar::-webkit-scrollbar-track {
          background: rgba(51, 65, 85, 0.3);
          border-radius: 3px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb,
        .custom-modal-scrollbar::-webkit-scrollbar-thumb {
          background: linear-gradient(to bottom, #0891b2, #1e40af);
          border-radius: 3px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb:hover,
        .custom-modal-scrollbar::-webkit-scrollbar-thumb:hover {
          background: linear-gradient(to bottom, #0e7490, #1d4ed8);
        }

        /* Main page scrollbar */
        ::-webkit-scrollbar {
          width: 8px;
        }

        ::-webkit-scrollbar-track {
          background: rgba(15, 23, 42, 0.5);
          border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb {
          background: linear-gradient(to bottom, #0891b2, #1e40af);
          border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
          background: linear-gradient(to bottom, #0e7490, #1d4ed8);
        }

        @keyframes flyLetter {
          0%, 100% {
            transform: translateY(0px) rotate(0deg);
            opacity: 1;
          }
          25% {
            transform: translateY(-10px) rotate(5deg);
            opacity: 0.8;
          }
          50% {
            transform: translateY(5px) rotate(-3deg);
            opacity: 0.9;
          }
          75% {
            transform: translateY(-8px) rotate(2deg);
            opacity: 0.7;
          }
        }

        @keyframes windParticle {
          0% {
            transform: translateX(0) translateY(0) scale(1);
            opacity: 0.8;
          }
          50% {
            transform: translateX(30px) translateY(-8px) scale(0.8);
            opacity: 0.4;
          }
          100% {
            transform: translateX(60px) translateY(3px) scale(0.6);
            opacity: 0;
          }
        }

        @keyframes flyEnvelope {
          0% {
            transform: translateX(0) translateY(0) rotate(0deg);
            opacity: 0.8;
          }
          25% {
            transform: translateX(20px) translateY(-15px) rotate(10deg);
            opacity: 1;
          }
          50% {
            transform: translateX(40px) translateY(5px) rotate(-5deg);
            opacity: 0.9;
          }
          75% {
            transform: translateX(60px) translateY(-10px) rotate(8deg);
            opacity: 0.7;
          }
          100% {
            transform: translateX(80px) translateY(0px) rotate(0deg);
            opacity: 0.3;
          }
        }
      `}</style>
    </div>
  )
}
