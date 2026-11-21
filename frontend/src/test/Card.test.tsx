import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/Card";

describe("Card component", () => {
  it("renders full card hierarchy", () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Test Card Title</CardTitle>
          <CardDescription>Test Description</CardDescription>
        </CardHeader>
        <CardContent>Main content body</CardContent>
        <CardFooter>Footer note</CardFooter>
      </Card>
    );

    expect(screen.getByText("Test Card Title")).toBeInTheDocument();
    expect(screen.getByText("Test Description")).toBeInTheDocument();
    expect(screen.getByText("Main content body")).toBeInTheDocument();
    expect(screen.getByText("Footer note")).toBeInTheDocument();
  });
});
