import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'serif'
matplotlib.rcParams['mathtext.fontset'] = 'cm'

blowup = [2, 4, 8]
proof_size = [600, 366, 293]

fig, ax = plt.subplots(figsize=(4, 3))
ax.plot(blowup, proof_size, 'o-', color='#1f77b4')
ax.set_xlabel('Blowup factor')
ax.set_ylabel('Proof size (KB)')
ax.set_xticks(blowup)

fig.tight_layout()
plt.savefig('tesi/images/blowup_size.pdf', bbox_inches='tight')
print('Done')