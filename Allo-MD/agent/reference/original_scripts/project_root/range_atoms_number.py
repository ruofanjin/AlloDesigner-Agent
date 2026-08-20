ranges = "5759-5799,5811-5853,5944-5962,6015-6033,6676-6808"
expanded = []

for part in ranges.split(','):
    if '-' in part:
        start, end = map(int, part.split('-'))
        expanded.extend(range(start, end + 1))
    else:
        expanded.append(int(part))

result = ",".join(map(str, expanded))
print(result)