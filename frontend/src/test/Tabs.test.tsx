import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/Tabs";

describe("Tabs component", () => {
  it("switches tabs and reveals corresponding content", () => {
    render(
      <Tabs defaultValue="tab1">
        <TabsList>
          <TabsTrigger value="tab1">First</TabsTrigger>
          <TabsTrigger value="tab2">Second</TabsTrigger>
        </TabsList>
        <TabsContent value="tab1">First panel content</TabsContent>
        <TabsContent value="tab2">Second panel content</TabsContent>
      </Tabs>
    );

    expect(screen.getByText("First panel content")).toBeInTheDocument();
    expect(screen.queryByText("Second panel content")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Second" }));

    expect(screen.queryByText("First panel content")).not.toBeInTheDocument();
    expect(screen.getByText("Second panel content")).toBeInTheDocument();
  });
});
