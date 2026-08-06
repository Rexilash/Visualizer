import 'package:flutter/material.dart';

class ColorPickerSection extends StatelessWidget {
  final Color primaryColor;
  final Color secondaryColor;
  final Color tertiaryColor;
  final Color bgColor;
  final Function(String label, Color color) onColorChanged;

  const ColorPickerSection({
    super.key,
    required this.primaryColor,
    required this.secondaryColor,
    required this.tertiaryColor,
    required this.bgColor,
    required this.onColorChanged,
  });

  void _pickColor(BuildContext context, String label, Color currentColor, ValueChanged<Color> onSelected) {
    final List<Color> colorPalette = [
      const Color(0xFFFF0096),
      const Color(0xFF00FFFF),
      const Color(0xFF0064FF),
      const Color(0xFF0F0F14),
      Colors.purpleAccent,
      Colors.amberAccent,
      Colors.greenAccent,
      Colors.deepOrangeAccent,
      Colors.black,
      Colors.white,
    ];

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Select $label Color'),
        content: Wrap(
          spacing: 12,
          runSpacing: 12,
          children: colorPalette.map((color) {
            return GestureDetector(
              onTap: () {
                onSelected(color);
                Navigator.pop(context);
              },
              child: CircleAvatar(
                backgroundColor: color,
                radius: 20,
                child: currentColor == color
                    ? Icon(
                        Icons.check,
                        color: color.computeLuminance() > 0.5 ? Colors.black : Colors.white,
                      )
                    : null,
              ),
            );
          }).toList(),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final chips = [
      (label: 'Primary', color: primaryColor),
      (label: 'Secondary', color: secondaryColor),
      (label: 'Tertiary', color: tertiaryColor),
      (label: 'BG', color: bgColor),
    ];

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceAround,
      children: chips.map((chip) {
        return InkWell(
          onTap: () => _pickColor(
            context,
            chip.label,
            chip.color,
            (selectedColor) => onColorChanged(chip.label, selectedColor),
          ),
          borderRadius: BorderRadius.circular(20),
          child: Padding(
            padding: const EdgeInsets.all(4.0),
            child: Column(
              children: [
                CircleAvatar(
                  backgroundColor: chip.color,
                  radius: 18,
                ),
                const SizedBox(height: 4),
                Text(chip.label, style: const TextStyle(fontSize: 11)),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }
}