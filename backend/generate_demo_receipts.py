import os
import cv2
import numpy as np

def create_receipt_image(filename, lines, output_dir):
    # Create a blank white page (600x800) simulating a receipt slip
    img = np.ones((850, 500, 3), dtype=np.uint8) * 255
    
    # Draw a thin grey border around the paper
    cv2.rectangle(img, (5, 5), (495, 845), (220, 220, 220), 2)
    
    # Add a receipt banner styling (black bar at the top)
    cv2.rectangle(img, (10, 10), (490, 80), (15, 23, 42), -1)
    
    # Header text
    cv2.putText(img, "EDULEDGER RECEIPT PIPELINE", (50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
    
    # Draw paper receipt items
    y = 130
    # Vendor Title
    cv2.putText(img, lines[0], (30, y), cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 0, 0), 2, cv2.LINE_AA)
    y += 40
    
    # Divider line
    cv2.line(img, (20, y), (480, y), (180, 180, 180), 1)
    y += 30
    
    # Date & Submitter Info
    for line in lines[1:3]:
        cv2.putText(img, line, (35, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1, cv2.LINE_AA)
        y += 25
        
    # Divider line
    y += 10
    cv2.line(img, (20, y), (480, y), (180, 180, 180), 1)
    y += 35
    
    # Items
    for line in lines[3:-1]:
        if "TOTAL" in line or "AMOUNT" in line:
            # Draw double line for total
            cv2.line(img, (20, y - 15), (480, y - 15), (100, 100, 100), 1)
            cv2.line(img, (20, y - 10), (480, y - 10), (100, 100, 100), 1)
            cv2.putText(img, line, (35, y), cv2.FONT_HERSHEY_DUPLEX, 0.65, (15, 23, 42), 2, cv2.LINE_AA)
        else:
            cv2.putText(img, line, (35, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (30, 30, 30), 1, cv2.LINE_AA)
        y += 35
        
    # Draw a mock barcode at the bottom
    barcode_y = 780
    cv2.putText(img, "*EDULEDGER-DEMO-PIPELINE*", (120, barcode_y + 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (120, 120, 120), 1, cv2.LINE_AA)
    
    # Draw simple vertical barcode bars
    x = 100
    while x < 400:
        bar_w = np.random.choice([2, 4, 6, 8])
        gap = np.random.choice([3, 5, 7])
        cv2.rectangle(img, (x, barcode_y), (x + bar_w, barcode_y + 25), (0, 0, 0), -1)
        x += bar_w + gap
        
    os.makedirs(output_dir, exist_ok=True)
    full_path = os.path.join(output_dir, filename)
    cv2.imwrite(full_path, img)
    print(f"Receipt image generated: {full_path}")

def generate_all():
    output_dir = os.path.join(os.path.dirname(__file__), "uploads")
    
    # 1. Textbooks receipt
    create_receipt_image(
        "receipt_textbooks.png",
        [
            "SCHOLASTIC BOOKS INC.",
            "Invoice #: 98231",
            "Date: 2026-07-06",
            "Item 1: English Literature Grade 9 (15x)  $300.00",
            "Item 2: Mathematics Standard Vol 2 (5x)   $150.00",
            "TOTAL AMOUNT: $450.00",
            "Payment Mode: Corporate Visa Credit"
        ],
        output_dir
    )
    
    # 2. Science Supplies
    create_receipt_image(
        "receipt_science_supplies.png",
        [
            "LABCORP ACADEMIC LABS",
            "Invoice #: L-9982",
            "Date: 2026-07-05",
            "Item 1: Glass Beakers 500ml (20x)          $80.00",
            "Item 2: Glass Pipettes Pack (2x)           $30.00",
            "Item 3: Nitrile Protective Gloves (5x)     $60.00",
            "SUBTOTAL: $170.00",
            "TAX (GST 9.1%): $15.50",
            "TOTAL AMOUNT PAID: $185.50"
        ],
        output_dir
    )
    
    # 3. Sports Outfit
    create_receipt_image(
        "receipt_sports.png",
        [
            "DECATHLON SCHOOL OUTFITTERS",
            "Invoice #: D-7721",
            "Date: 2026-07-02",
            "Item 1: Training Soccer Balls (10x)        $200.00",
            "Item 2: Double Action Ball Air Pump         $20.00",
            "Item 3: Soccer Agility Cones Set (5x)     $100.00",
            "TOTAL CHARGED: $320.00"
        ],
        output_dir
    )
    
    # 4. Staff lunch
    create_receipt_image(
        "receipt_lunch.png",
        [
            "DOWNTOWN CATERING SERVICES",
            "Invoice #: DC-33821",
            "Date: 2026-07-01",
            "Item 1: Deluxe Staff Sandwich Platters     $50.00",
            "Item 2: Coffee Urn & Beverage Setup        $25.00",
            "GRAND TOTAL DUE: $75.00",
            "Status: PAID IN FULL - THANK YOU!"
        ],
        output_dir
    )

if __name__ == "__main__":
    generate_all()
