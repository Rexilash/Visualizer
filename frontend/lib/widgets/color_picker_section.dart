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

  void _openFullColorPicker(BuildContext context, String label, Color currentColor, ValueChanged<Color> onSelected) {
    Color selectedColor = currentColor;
    final hexController = TextEditingController(
      text: currentColor.value.toRadixString(16).padLeft(8, '0').substring(2).toUpperCase(),
    );

    showDialog(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setPickerState) {
            return AlertDialog(
              title: Text('Custom $label Color'),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // Color Preview Box
                    Container(
                      height: 60,
                      width: double.infinity,
                      decoration: BoxDecoration(
                        color: selectedColor,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.white24),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // HEX Code Field
                    TextField(
                      controller: hexController,
                      decoration: const InputDecoration(
                        labelText: 'Hex Code (#)',
                        border: OutlineInputBorder(),
                        contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      ),
                      onChanged: (val) {
                        final hex = val.replaceAll('#', '');
                        if (hex.length == 6) {
                          final intColor = int.tryParse('FF$hex', radix: 16);
                          if (intColor != null) {
                            setPickerState(() {
                              selectedColor = Color(intColor);
                            });
                          }
                        }
                      },
                    ),
                    const SizedBox(height: 12),

                    // RGB Channel Sliders
                    _buildChannelSlider(
                      label: 'Red',
                      value: selectedColor.red.toDouble(),
                      activeColor: Colors.redAccent,
                      onChanged: (v) {
                        setPickerState(() {
                          selectedColor = selectedColor.withRed(v.toInt());
                          hexController.text = selectedColor.value.toRadixString(16).padLeft(8, '0').substring(2).toUpperCase();
                        });
                      },
                    ),
                    _buildChannelSlider(
                      label: 'Green',
                      value: selectedColor.green.toDouble(),
                      activeColor: Colors.greenAccent,
                      onChanged: (v) {
                        setPickerState(() {
                          selectedColor = selectedColor.withGreen(v.toInt());
                          hexController.text = selectedColor.value.toRadixString(16).padLeft(8, '0').substring(2).toUpperCase();
                        });
                      },
                    ),
                    _buildChannelSlider(
                      label: 'Blue',
                      value: selectedColor.blue.toDouble(),
                      activeColor: Colors.blueAccent,
                      onChanged: (v) {
                        setPickerState(() {
                          selectedColor = selectedColor.withBlue(v.toInt());
                          hexController.text = selectedColor.value.toRadixString(16).padLeft(8, '0').substring(2).toUpperCase();
                        });
                      },
                    ),
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Cancel'),
                ),
                ElevatedButton(
                  onPressed: () {
                    onSelected(selectedColor);
                    Navigator.pop(context);
                  },
                  child: const Text('Apply Color'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  Widget _buildChannelSlider({
    required String label,
    required double value,
    required Color activeColor,
    required ValueChanged<double> onChanged,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
            Text(value.toInt().toString(), style: const TextStyle(fontSize: 12)),
          ],
        ),
        Slider(
          value: value,
          min: 0,
          max: 255,
          activeColor: activeColor,
          onChanged: onChanged,
        ),
      ],
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
          onTap: () => _openFullColorPicker(
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
                  child: Icon(Icons.colorize, size: 14, color: chip.color.computeLuminance() > 0.5 ? Colors.black : Colors.white),
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