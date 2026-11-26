item = 0.70
rate = 1.05

tax = item * rate
total = item + tax

print("Item: ", "{:.2f}".format(item))
print("Tax: ", "{:.2f}".format(tax))
print("Total: ", "{:.2f}".format(total))
print(total)


print("Item: ", "{:.20f}".format(item))
print("Tax: ", "{:.20f}".format(tax))
print("Total: ", "{:.20f}".format(total))
