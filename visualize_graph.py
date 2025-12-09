"""Generate and save the LangGraph workflow visualization."""

from src.agents.graph import research_graph


def save_graph_visualization(output_path: str = "workflow_graph.png"):
    """
    Generate and save the LangGraph workflow visualization.
    
    Args:
        output_path: Path where the PNG image will be saved
    """
    try:
        # Get the graph visualization as PNG bytes
        png_bytes = research_graph.get_graph(xray=True).draw_mermaid_png()
        
        # Write the bytes to a file
        with open(output_path, "wb") as f:
            f.write(png_bytes)
        
        print(f"✓ Graph visualization saved to: {output_path}")
        
    except Exception as e:
        print(f"✗ Error generating graph visualization: {e}")
        raise


if __name__ == "__main__":
    save_graph_visualization()

