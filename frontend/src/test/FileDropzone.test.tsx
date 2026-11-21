import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { FileDropzone } from "@/components/ui/FileDropzone";

describe("FileDropzone component", () => {
  it("validates file extension and accepts supported file", () => {
    const handleAccepted = vi.fn();
    render(<FileDropzone onFileAccepted={handleAccepted} />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input).toBeInTheDocument();

    const validFile = new File(["valid manuscript content"], "paper.pdf", {
      type: "application/pdf",
    });

    fireEvent.change(input, { target: { files: [validFile] } });

    expect(handleAccepted).toHaveBeenCalledWith(validFile);
    expect(screen.getByText("paper.pdf")).toBeInTheDocument();
  });

  it("rejects unsupported file format", () => {
    const handleAccepted = vi.fn();
    render(<FileDropzone onFileAccepted={handleAccepted} allowedExtensions={[".pdf", ".docx", ".txt"]} />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    const invalidFile = new File(["executable"], "script.exe", {
      type: "application/x-msdownload",
    });

    fireEvent.change(input, { target: { files: [invalidFile] } });

    expect(handleAccepted).not.toHaveBeenCalled();
    expect(screen.getByText(/Invalid file type/i)).toBeInTheDocument();
  });

  it("rejects files exceeding size limit", () => {
    const handleAccepted = vi.fn();
    render(
      <FileDropzone
        onFileAccepted={handleAccepted}
        maxSizeBytes={1024 * 1024} // 1 MB limit
      />
    );

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    // Create 2 MB dummy file
    const oversizedFile = new File([new ArrayBuffer(2 * 1024 * 1024)], "huge.docx", {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });

    fireEvent.change(input, { target: { files: [oversizedFile] } });

    expect(handleAccepted).not.toHaveBeenCalled();
    expect(screen.getByText(/File is too large/i)).toBeInTheDocument();
  });
});
