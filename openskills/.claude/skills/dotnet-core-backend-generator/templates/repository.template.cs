using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using System.Threading;
using System.Threading.Tasks;
using System.Collections.Generic;
using System.Linq;

namespace Backend.Infrastructure.Repositories
{
    public class {{EntityName}}Repository : I{{EntityName}}Repository
    {
        private readonly ApplicationDbContext _context;
        private readonly ILogger<{{EntityName}}Repository> _logger;

        public {{EntityName}}Repository(ApplicationDbContext context, ILogger<{{EntityName}}Repository> logger)
        {
            _context = context;
            _logger = logger;
        }

        public async Task<{{EntityName}}> AddAsync({{EntityName}} entity, CancellationToken cancellationToken = default)
        {
            _context.Add(entity);
            await _context.SaveChangesAsync(cancellationToken);
            return entity;
        }

        public async Task DeleteAsync(int id, CancellationToken cancellationToken = default)
        {
            var item = await _context.{{EntityName}}s.FindAsync(new object[] { id }, cancellationToken);
            if (item == null) return;
            item.IsDeleted = true;
            await _context.SaveChangesAsync(cancellationToken);
        }

        public async Task<IEnumerable<{{EntityName}}>> GetAllAsync(CancellationToken cancellationToken = default)
        {
            return await _context.{{EntityName}}s.AsNoTracking().Where(x => !x.IsDeleted).ToListAsync(cancellationToken);
        }

        public async Task<{{EntityName}}?> GetByIdAsync(int id, CancellationToken cancellationToken = default)
        {
            return await _context.{{EntityName}}s.AsNoTracking().FirstOrDefaultAsync(x => x.Id == id && !x.IsDeleted, cancellationToken);
        }

        public async Task UpdateAsync({{EntityName}} entity, CancellationToken cancellationToken = default)
        {
            _context.Update(entity);
            await _context.SaveChangesAsync(cancellationToken);
        }
    }
}
