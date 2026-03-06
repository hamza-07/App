"""
Calculation Utilities for Quotation Module
All calculations based on corrugation factory formulas
"""

from decimal import Decimal, ROUND_HALF_UP


# Conversion factors
MM_TO_INCHES = Decimal('25.4')
CM_TO_INCHES = Decimal('2.54')

def convert_to_inches(value, unit):
    """Convert length to inches"""
    value = Decimal(str(value))
    if unit.lower() == 'mm':
        return (value / MM_TO_INCHES).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    elif unit.lower() == 'cm':
        return (value / CM_TO_INCHES).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    elif unit.lower() == 'inches' or unit.lower() == 'inch':
        return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    else:
        return value

def calculate_roll_size(width, height):
    """Formula: Roll Size = (W + H) + 1"""
    return (Decimal(str(width)) + Decimal(str(height)) + Decimal('1')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def calculate_cutting_size(length, width, pcs):
    """
    Formula for 1 pcs: (L + W) * 2 + 2
    Formula for 2 pcs: (L + W) + 4
    """
    if pcs == 1:
        return ((Decimal(str(length)) + Decimal(str(width))) * Decimal('2') + Decimal('2')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    else:  # 2 pcs
        return ((Decimal(str(length)) + Decimal(str(width))) + Decimal('4')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def calculate_sheets_per_roll(cutting_size):
    """Formula: (2400 / Cutting Size) - 1"""
    roll_length = Decimal('2400')  # Standard roll length in inches
    sheets = (roll_length / Decimal(str(cutting_size))) - Decimal('1')
    return sheets.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def calculate_paper_cost(roll_size, cutting_size, gsm, paper_rate_per_kg):
    """
    Formula: ((Roll Size * Cutting Size * GSM) / 1,550,000) * Paper Rate
    """
    numerator = Decimal(str(roll_size)) * Decimal(str(cutting_size)) * Decimal(str(gsm))
    denominator = Decimal('1550000')
    paper_weight_kg = numerator / denominator
    cost = paper_weight_kg * Decimal(str(paper_rate_per_kg))
    return cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def calculate_silicate_rate(roll_size, cutting_size, ply):
    """
    Formula: Roll Size * Cutting Size * 0.0035 * Ply Factor
    Ply Factor: 3-ply = 1, 5-ply = 2, 7-ply = 3
    """
    base_rate = Decimal('0.0035')
    ply_factor = {3: 1, 5: 2, 7: 3}.get(ply, 1)
    rate = Decimal(str(roll_size)) * Decimal(str(cutting_size)) * base_rate * Decimal(str(ply_factor))
    return rate.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def calculate_roll_cost_per_sheet(roll_size, roll_rate, number_of_sheets):
    """Formula: (Roll Size * Roll Rate) / Number of Cutting Sheets"""
    total_roll_cost = Decimal(str(roll_size)) * Decimal(str(roll_rate))
    cost_per_sheet = total_roll_cost / Decimal(str(number_of_sheets))
    return cost_per_sheet.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def calculate_quotation_item_cost(item_data, settings):
    from models import PaperGrade, RollGrade
    """
    Calculate total cost for a quotation item
    Returns: {
        'roll_size': ...,
        'cutting_size': ...,
        'sheets_per_roll': ...,
        'roll_cost_per_sheet': ...,
        'paper_costs': {...},
        'silicate_cost': ...,
        'printing_cost': ...,
        'labour_cost': ...,
        'cartage_cost': ...,
        'subtotal': ...,
        'profit_margin': ...,
        'unit_rate': ...,
        'total_amount': ...
    }
    """
    # Convert dimensions to inches
    length = convert_to_inches(item_data['length'], item_data['unit'])
    width = convert_to_inches(item_data['width'], item_data['unit'])
    height = convert_to_inches(item_data['height'], item_data['unit'])
    ply = int(item_data['ply'])
    pcs = int(item_data.get('pcs', 1))
    
    # Calculate roll and cutting sizes
    roll_size = calculate_roll_size(width, height)
    cutting_size = calculate_cutting_size(length, width, pcs)
    sheets_per_roll = calculate_sheets_per_roll(cutting_size)
    
    # Get material rates
    roll_grade = RollGrade.query.get(item_data['flute1_roll_id'])
    roll_rate = Decimal(str(roll_grade.rate_per_roll)) if roll_grade else Decimal('0')
    
    # Calculate roll cost per sheet
    roll_cost_per_sheet = calculate_roll_cost_per_sheet(roll_size, roll_rate, sheets_per_roll)
    
    # Calculate paper costs for each layer
    paper_costs = {}
    total_paper_cost = Decimal('0')
    
    # Top paper
    if item_data.get('top_paper_id'):
        top_paper = PaperGrade.query.get(item_data['top_paper_id'])
        if top_paper:
            cost = calculate_paper_cost(roll_size, cutting_size, top_paper.gsm, top_paper.rate_per_kg)
            paper_costs['top'] = float(cost)
            total_paper_cost += cost
    
    # Middle paper (for 5-ply and 7-ply)
    if ply >= 5 and item_data.get('middle_paper_id'):
        middle_paper = PaperGrade.query.get(item_data['middle_paper_id'])
        if middle_paper:
            cost = calculate_paper_cost(roll_size, cutting_size, middle_paper.gsm, middle_paper.rate_per_kg)
            paper_costs['middle'] = float(cost)
            total_paper_cost += cost
    
    # Bottom paper
    if item_data.get('bottom_paper_id'):
        bottom_paper = PaperGrade.query.get(item_data['bottom_paper_id'])
        if bottom_paper:
            cost = calculate_paper_cost(roll_size, cutting_size, bottom_paper.gsm, bottom_paper.rate_per_kg)
            paper_costs['bottom'] = float(cost)
            total_paper_cost += cost
    
    # Additional paper layers for 7-ply
    if ply == 7 and item_data.get('middle_paper_id'):
        # Second middle layer
        cost = calculate_paper_cost(roll_size, cutting_size, middle_paper.gsm, middle_paper.rate_per_kg)
        paper_costs['middle2'] = float(cost)
        total_paper_cost += cost
    
    # Additional roll costs for multiple plies
    if ply >= 5 and item_data.get('flute2_roll_id'):
        flute2_roll = RollGrade.query.get(item_data['flute2_roll_id'])
        if flute2_roll:
            additional_roll_cost = calculate_roll_cost_per_sheet(roll_size, flute2_roll.rate_per_roll, sheets_per_roll)
            roll_cost_per_sheet += additional_roll_cost
    
    if ply == 7 and item_data.get('flute3_roll_id'):
        flute3_roll = RollGrade.query.get(item_data['flute3_roll_id'])
        if flute3_roll:
            additional_roll_cost = calculate_roll_cost_per_sheet(roll_size, flute3_roll.rate_per_roll, sheets_per_roll)
            roll_cost_per_sheet += additional_roll_cost
    
    # Calculate silicate cost
    silicate_cost = calculate_silicate_rate(roll_size, cutting_size, ply)
    
    # Additional costs
    printing_cost = Decimal(str(item_data.get('printing_cost', 0)))
    labour_cost = Decimal(str(item_data.get('labour_cost', settings.labour_rate)))
    cartage_cost = Decimal(str(item_data.get('cartage_cost', settings.cartage_rate)))
    
    # Subtotal before profit
    subtotal = roll_cost_per_sheet + total_paper_cost + silicate_cost + printing_cost + labour_cost + cartage_cost
    
    # Apply profit margin
    profit_margin = settings.profit_margin_percent / Decimal('100')
    unit_rate = subtotal * (Decimal('1') + profit_margin)
    unit_rate = unit_rate.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Total amount
    quantity = int(item_data.get('quantity', 1))
    total_amount = unit_rate * Decimal(str(quantity))
    total_amount = total_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    return {
        'roll_size': float(roll_size),
        'cutting_size': float(cutting_size),
        'sheets_per_roll': float(sheets_per_roll),
        'roll_cost_per_sheet': float(roll_cost_per_sheet),
        'paper_costs': paper_costs,
        'total_paper_cost': float(total_paper_cost),
        'silicate_cost': float(silicate_cost),
        'printing_cost': float(printing_cost),
        'labour_cost': float(labour_cost),
        'cartage_cost': float(cartage_cost),
        'subtotal': float(subtotal),
        'profit_margin_percent': float(settings.profit_margin_percent),
        'unit_rate': float(unit_rate),
        'total_amount': float(total_amount)
    }

def create_quotation_item(quotation_id, item_data):
    """Create QuotationItem from calculated data"""
    from models import QuotationItem, Settings
    
    calc_result = calculate_quotation_item_cost(item_data, Settings.get_settings())
    
    # Build description
    length = convert_to_inches(item_data['length'], item_data['unit'])
    width = convert_to_inches(item_data['width'], item_data['unit'])
    height = convert_to_inches(item_data['height'], item_data['unit'])
    description = f"{item_data['ply']}-Ply Corrugated Carton Size: {length}\" x {width}\" x {height}\""
    
    if item_data.get('printing'):
        description += f" (Printed - {item_data.get('printing_sides', 0)} sides)"
    
    item = QuotationItem(
        quotation_id=quotation_id,
        description=description,
        length=length,
        width=width,
        height=height,
        ply=int(item_data['ply']),
        printing=bool(item_data.get('printing', False)),
        printing_sides=int(item_data.get('printing_sides', 0)),
        pcs=int(item_data.get('pcs', 1)),
        joint_type=item_data.get('joint_type', 'Glue'),
        quantity=int(item_data['quantity']),
        top_paper_id=item_data.get('top_paper_id'),
        middle_paper_id=item_data.get('middle_paper_id'),
        bottom_paper_id=item_data.get('bottom_paper_id'),
        flute1_roll_id=item_data.get('flute1_roll_id'),
        flute2_roll_id=item_data.get('flute2_roll_id'),
        flute3_roll_id=item_data.get('flute3_roll_id'),
        unit_rate=calc_result['unit_rate'],
        total_amount=calc_result['total_amount'],
        printing_cost=calc_result['printing_cost'],
        labour_cost=calc_result['labour_cost'],
        cartage_cost=calc_result['cartage_cost']
    )
    
    return item
